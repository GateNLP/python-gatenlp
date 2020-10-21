from gatenlp.processing.pipeline import _has_method

__pdoc__ = {
    "Annotator.__call__": True
}


class SerialCorpusExecutor:
    """
    Runs a pipeline on an iterable of documents and creates another iterable of documents.
    If inplace=True, the original iterable must be an object that can be enumerated and where
    each element can be accessed and replaced by its enumeration number: `doc=corpus[i]`
    `corpus[i] = doc`.
    """
    def __init__(self,
                 input_corpus,
                 annotator,
                 output_corpus=None,
                 inplace=False,
                 ):
        """
        Creates an Executor to run an annotator on an iterator of documents. If an output corpus is
        specified, the returned documents are added to the output corpus and the inplace parameter is ignored.

        If no output corpus is specified, then if inplace is True, the processing result is stored back into
        the input corpus which mast support setting an element by id. If the annotator returns a list of documents
        or None, that is also stored back to where the original document was. In most cases, if documents should get
        stored back, the Annotator should return the original document.

        If no output corpus is specified and
        inplace is False, the documents are processed, but the returned documents are discarded (this can be
        useful if the annotator is really just something that is called for a side-effect like sending or storing).

        If an output corpus is specified, the returned document(s) are added one by one to it using the
        `append` or `add` method of the corpus.

        Args:
            input_corpus: the source of documents to iterate over. If inplace is True and not output corpus is
              specified this must all to assign the processing result back to the corpus, e.g. `corpus[i]=result`.
            annotator: the callable to run on each document. If this is an instance of Annotator, the additional
              methods start, finish, and reduce are called as appropriate
            output_corpus: if specified the result documents are added to this one by one, if an annotator returns
              a list, then the list elements are added. If the corpus has the method "append" it is used, otherwise
              the method "add" is expected.
            inplace: if no output corpus is specified and this is True, then results are assigned back to the
              input corpus.
        """
        self.input_corpus = input_corpus
        # check how we can add to the output corps
        if output_corpus:
            adder = getattr(output_corpus, "append", None)
            if adder is None:
                adder = getattr(output_corpus, "add", None)
            if adder is None or not callable(adder):
                raise Exception("Output corpus does not have a callable 'append' or 'add' method")
            self.corpus_adder = adder
        elif inplace:
            adder = getattr(input_corpus, "__setitem__", None)
            if adder is None or not callable(adder):
                raise Exception("Input corpus cannot be assigned to")
        self.corpus_adder = adder
        if output_corpus is None and inplace:
            self.output_corpus = input_corpus
        else:
            self.output_corpus = output_corpus
            self.inplace = False
        self.annotator = annotator

    def __call__(self, **kwargs):
        if _has_method(self.annotator, "start"):
            self.annotator.init()
        for idx, doc in enumerate(self.input_corpus):
            ret = self.annotator(doc, **kwargs)
            if self.inplace:   # we need to assign the result as it is back to the corpus
                self.input_corpus[idx] = ret
            elif self.output_corpus:
                if ret is not None:
                    for d in ret:
                        self.output_corpus.append(d)
        if _has_method(self.annotator, "finish"):
            rets = self.annotator.init()
            return rets
        else:
            return None
        # NOTE: since this is single-threaded, no reduce call is necessary!

