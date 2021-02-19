from gatenlp.processing.pipeline import _has_method
from gatenlp.utils import init_logger

__pdoc__ = {"Annotator.__call__": True}


class SerialCorpusExecutor:
    """
    Runs a pipeline on either a corpus, where each document gets in the corpus gets processed and stored back
    in turn, or on a source and destination, where each document from the source gets processed and all documents
    the are the result of processing get appended to the destination.
    """

    def __init__(
        self,
        annotator,
        corpus=None,
        source=None,
        destination=None,
        readonly=False,
        exit_on_error=False,
        logger=None,
    ):
        """
        Creates an Executor to run an annotator on either a corpus or a document source. If a corpus is specified,
        and no destination is specified,
        the document passed on to the annotator must be returned by the annotator and gets stored back into the
        corpus, unless readonly is True.

        If a corpus is specified and a destination is specified, the corpus is iterated over in sequence and
        documents are processed by the annotator and all documents returned by the annotator are appended to the
        destination.

        If a document source is processed, the document gets processed and the annotator can return zero,
        one or several documents which are appended to the destination unless readonly is set to True.

        An exception is thrown if both a courpus and a source are specified.

        Args:
            annotator: the callable to run on each document. If this is an instance of Annotator, the additional
              methods start, finish, and reduce are called as appropriate
            corpus: the corpus to process.
            source: a document source to process. Corpus and source are mutually exclusive.
            destination: if specified, the result documents are appended to the destination unless
              readonly is True.
            readonly: if True, nothing is saved back to the corpus or appended to the destination.
            exit_on_error: if True pass on exception, otherwise just log, use None and continue
            logger: logger to use, if None, uses a default logger

        Returns:
            if annotator has a finish() method calls it and returns whatever it returns, otherwise None
        """
        if (corpus is None and source is None) or (
            corpus is not None and source is not None
        ):
            raise Exception("Exactly one of corpus or source must be specified")
        self.corpus = corpus
        self.source = source
        self.destination = destination
        self.annotator = annotator
        self.readonly = readonly
        self.exit_on_error = exit_on_error
        self.n_in = 0
        self.n_none = 0  # number of None items from the corpus/source, ignored
        self.n_out = 0
        self.n_err = 0
        self.n_ok = 0
        if logger:
            self.logger = logger
        else:
            self.logger = init_logger(__name__)

    def __call__(self, **kwargs):
        if _has_method(self.annotator, "start"):
            self.annotator.start()
        if self.corpus is not None:
            for idx, doc in enumerate(self.corpus):
                self.n_in += 1
                if doc is None:
                    self.n_none += 1
                    continue
                try:
                    ret = self.annotator(doc, **kwargs)
                    self.n_ok += 1
                except Exception as ex:
                    self.n_err += 1
                    if self.exit_on_error:
                        raise ex
                    else:
                        docname = doc.name
                        self.logger.error(f"Error processing document {idx}/{docname}",
                                          exc_info=ex, stack_info=True)
                        continue
                if ret is None:
                    self.n_none += 1
                if self.destination is None:
                    if ret is None:
                        self.n_out += 1
                        continue
                    if isinstance(ret, list):
                        if len(ret) != 1:
                            raise Exception(
                                "Cannot update corpus if Annotator returns not exactly one document"
                            )
                        else:
                            ret = ret[0]
                    self.corpus[idx] = ret
                else:
                    if ret is not None:
                        if isinstance(ret, list):
                            for d in ret:
                                self.destination.append(d)
                                self.n_out += 1
                        else:
                            self.destination.append(ret)
                            self.n_out += 1
        else:
            idx = -1
            for doc in self.source:
                idx += 1
                self.n_in += 1
                if doc is None:
                    self.n_none += 1
                    continue
                try:
                    ret = self.annotator(doc, **kwargs)
                    self.n_ok += 1
                except Exception as ex:
                    self.n_err += 1
                    if self.exit_on_error:
                        raise ex
                    else:
                        docname = doc.name
                        self.logger.error(f"Error processing document {idx}/{docname}",
                                          exc_info=ex, stack_info=True)
                        continue
                if ret is None:
                    self.n_none += 1
                if self.destination is not None:
                    if isinstance(ret, list):
                        for d in ret:
                            self.destination.append(d)
                            self.n_out += 1
                    else:
                        self.destination.append(ret)
                        self.n_out += 1
        if _has_method(self.annotator, "finish"):
            rets = self.annotator.finish()
            return rets
        else:
            return None
        # NOTE: since this is single-threaded, no reduce call is necessary!
