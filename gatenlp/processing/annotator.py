"""
Module with the base class and supporting functions for all annotators.
Any callable that can be called by passing a document can be used as an annotator,
but the base class "Annotator" defined in here is designed to allow for a more
flexible approach to do things.
"""
from abc import ABC, abstractmethod

__pdoc__ = {"Annotator.__call__": True}


class Annotator(ABC):
    @abstractmethod
    def __call__(self, doc, **kwargs):
        """
        This method MUST get implemented in a concrete subclass to do the actual processing
        and annotation. It must accept a document and arbitrary keyword arguments and it must
        return either a document which may be the same or a different object than the document passed,
        or None or an empty list or a list of one or more documents. The method also may raise an
        exception.

        The semantics of returning None or an empty list are not strictly defined: this may be used to
        handle processing errors where documents which cannot be processed are quietly ignored or
        filtering.

        The method must accept arbitrary keyword arguments which will be passed on to sub-annotators and
        may be used to configure or parametrize processing.

        NOTE: some annotators may set or use special document features in order to handle
        document context or the document id when processing a corpus or streams where a document id
        is important.

        Args:
          doc: the document to process
          kwargs: any arguments to pass to the annotator or sub-annotators called by this annotator

        Returns:
            a document, None, or a possibly empty list of documents
        """
        raise Exception("This method must be implemented!")

    def pipe(self, documents, **kwargs):
        """
        If this method gets overridden, it should take an iterable of documents and yield processed documents.
        This allows for batching, caching, and other optimizations over streams of documents.
        If with_context is True, then the documents parameter should be an iterable over tuples (document, context).

        Args:
            documents: an iterable over documents or (document, context) tuples if with_context=True
            **kwargs: arbitrary other keyword arguments must be accepted

        Yields:
            processed documents
        """
        for el in documents:
            if el is not None:
                docordocs = self.__call__(el, **kwargs)
                if docordocs is not None:
                    if isinstance(docordocs, list):
                        for el in docordocs:
                            if el is not None:
                                yield el
                    else:
                        yield docordocs

    def start(self):
        """
        A method that gets called when processing starts, e.g. before the first document in
        corpus gets processed. This is invoked by an executor to initialize processing a batch
        of documents.

        This is different from initializing the Annotator: initializing may load large data which
        can be reused even if the same annotator instance is run several times over documents.
        """
        pass

    def finish(self):
        """
        A method that gets called when processing ends, e.g. when all documents of a corpus
        have been processed. It should return some result for processing the whole batch of documents
        it has seen - that result may be None.

        Returns:
            The overall result of processing all documents or None
        """
        pass

    def reduce(self, results):
        """
        A method that should know how to combine the results passed on in some collection into a
        single result. This method should behave like a static method, i.e. not make use of any
        data that is specific to the concrete instance.

        This can be used to combine corpus results obtained from several processes running on
        different parts of a corpus.

        This gets invoked by the executor if more than one instance of the annotator was run
        over separate sets of documents. If only a single instance was used, the result returned
        from finish is used directly.

        Args:
          results: an iterable of individual results over some documents each or None if no results are available.
             If no results have been passed back from the finish method of any of the processes, the executor should
             not call reduce, but if it does, reduce should accept None or an iterator of all None and return None.

        Returns:
            The combined overall result or None if there are no individual results
        """
        return results


class AnnotatorFunction(Annotator):
    def __init__(self, funct):
        self.funct = funct

    def __call__(self, doc, **kwargs):
        return self.funct(doc, **kwargs)
