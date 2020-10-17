"""
Base class and supporting functions for all annotators.
Any callable that can be called by passing a document can be used as an annotator,
but the base class "Annotator" defined in here is designed to allow for a more
flexible approach to do things.

One functionality we could also implement here is by implementing the annotator
call function to follow a basic monad pattern for stream processing: instead of
returning a document, return a list, which allows to represent: no document returned
(filtering), one document returned (update/replacement), more than one document
returned (functions like segmenting). However this clashes with the idea of
using this also to combine partial per-document results with merge.
"""

__pdoc__ = {
    "Annotator.__call__": True
}

class Annotator:
    def __call__(self, doc, **kwargs):
        """
        This method must get implemented in a concrete subclass to do the actual processing
        and annotation. It must accept a document and return a document which may be
        the same that got passed.
        If it returns a list of documents, all of them are used as processing results, if
        the list is empty, the processing does not yield a result.

        The method must accept arbitrary keyword arguments which will be used for handling
        non-standard situations.

        :param doc: the document to process
        :param kwargs:
        :return: a document or a list of documents
        """
        raise Exception("This method must be implemented!")

    def start(self):
        """
        A method that gets called when processing starts, e.g. before the first document in
        corpus gets processed. This is invoked by an executor to initialize processing a batch
        of documents.

        This is different from initializing the Annotator: initializing may load large data which
        can be reused even if the same annotator instance is run several times over documents.

        :return:
        """
        pass

    def finish(self):
        """
        A method that gets called when processing ends, e.g. when all documents of a corpus
        have been processed. It should return some result for processing the whole batch of documents
        it has seen - that result may be None.

        :return: result of processing documents or None
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

        :param resultlist: an iterable of individual results over some documents each
        :return: overal result
        """