"""
Base class and supporting functions for all annotators.
Any callable that cann be called by passing a document can be used as an annotator,
but the base class "Annotator" defined in here is designed to allow for a more
flexible approach to do things.

One functionality we could also implement here is by implementing the annotator
call function to follow a basic monad pattern for stream processing: instead of
returning a document, return a list, which allows to represent: no document returned
(filtering), one document returned (update/replacement), more than one document
returned (functions like segmenting). However this clashes with the idea of
using this also to combine partial per-document results with merge.
"""


class Annotator:
    def __call__(self, doc, **kwargs):
        """
        This method must get implemented in a concrete subclass to do the actual processing
        and annotation. It must accept a document and change the document annotations.
        The method must accept arbitrary keyword arguments which will be used for handling
        non-standard situations.
        :param doc: the document to process
        :param kwargs:
        :return:
        """
        raise Exception("This method must be implemented!")

    def merge(self, doc, docsorlogs):
        """
        A mthod that knows how to combine a collection of partial processing results into one document
        and returns that document. This is meant to be used in situations where parallelisation is
        done per document, so that several processes work on the same document in parallel. Each
        process creates their annotated document or changelog and this method should be able to combine
        all the partial results to create one result document.
        This should be implemented like a static method, not using any of the instance specific
        data.
        :param doc: the original input document
        :param docsorlogs: a collection of documents or changelogs where each element represents
        partial annotations carried out on the original document
        :return: the original document with the results from all the documents or changelogs combined
        """

    def start(self):
        """
        A method that gets called when processing starts, e.g. before the first document in
        corpus gets processed.
        :return:
        """
        pass

    def finish(self):
        """
        A mthod that gets called when processing ends, e.g. when all documents of a corpus
        have been processed.
        :return:
        """
        pass

    def result(self):
        """
        A method that can be used to return the result of processing a whole corpus or stream
        of documents, should only be called after finish() has been called.
        This should return the same results every time when it is called repeatedly after finish
        and before start() is called again.
        :return: corpus-wide processing results
        """

    def reduce(self, results):
        """
        A method that should know how to combine the results passed on in some collection into a
        single result. This method should behave like a static method, i.e. not make use of any
        data that is specific to the concrete instance.
        This can be used to combine corpus results obtained from several processes running on
        different parts of a corpus.
        :param resultlist:
        :return:
        """