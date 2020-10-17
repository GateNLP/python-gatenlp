from gatenlp.processing.pipeline import _has_method

__pdoc__ = {
    "Annotator.__call__": True
}


class SerialCorpusExecutor:
    """Runs a pipeline on an iterable of documents and creates another iterable of documents.
    If inplace=True, the original iterable must be an object that can be enumerated and where
    each element can be accessed and replaced by its enumeration number: `doc=corpus[i]`
    `corpus[i] = doc`.

    Args:

    Returns:

    """
    def __init__(self, input_corpus, annotator, output_corpus=None,):
        self.input_corpus = input_corpus
        if output_corpus is None:
            self.output_corpus = input_corpus
            self.inplace = True
        else:
            self.output_corpus = output_corpus
            self.inplace = False
        self.result = None
        self.annotator = annotator

    def __call__(self, **kwargs):
        if _has_method(self.annotator, "start"):
            self.annotator.init()
        for idx, doc in enumerate(self.corpus):
            ret = self.annotator(doc, **kwargs)
            if self.inplace:
                if isinstance(ret, list):
                    raise Exception("Annotator must not return list for inplace corpus")
                self.output_corpus[idx] = ret
            else:
                if isinstance(ret,list):
                    self.output_corpus.extend(ret)
                else:
                    self.output_corpus.append(ret)
        if _has_method(self.annotator, "finish"):
            rets = self.annotator.init()
            self.result = rets
        # NOTE: we only have one process/batch, so we do not need to reduce and just return the
        # results as is
        return self.result


