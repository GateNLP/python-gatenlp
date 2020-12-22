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
    def __call__(self, doc, context=None, **kwargs):
        """
        This method must get implemented in a concrete subclass to do the actual processing
        and annotation. It must accept a document and return a document which may or may not be
        the same that got passed.

        If it returns a list of documents, all of them are used as processing results, if
        the list is empty, the processing does not yield a result.

        The method must accept arbitrary keyword arguments which will be used for handling
        non-standard situations.

        Args:
          doc: the document to process
          context: some arbitrary context/data related to the document.
          kwargs: return: a document or a list of documents

        Returns:
            a document or a list of documents
        """
        raise Exception("This method must be implemented!")

    def pipe(self, documents, with_context=False, **kwargs):
        """
        If this method gets overridden, it should take an iterable of documents and yield processed documents.
        This allows for batching, caching, and other optimizations over streams of documents.
        If with_context is True, then the documents parameter should be an iterable over tuples (document, context).

        Args:
            documents: an iterable over documents or (document, context) tuples if with_context=True
            with_context: if True, the iterable is over (document, context) tuples
            **kwargs: arbitrary other keyword arguments must be accepted

        Yields:
            processed documents. If with_context is True, yields tuples (processed_document, context)
        """
        for el in documents:
            if with_context:
                doc, context = el
                doc, context = self.__call__(doc, context=context, **kwargs)
                yield doc, context
            else:
                doc, context = el, None
                doc = self.__call__(doc, **kwargs)
                yield doc

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
