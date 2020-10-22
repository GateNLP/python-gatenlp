"""
Module that defines base and implementation classes for representing document collections.

Corpus subclasses represent collections with a fixed number of documents, where each document can be
accessed and stored by its index number, much like lists/arrays of documents.

DocumentSource subclasses represent collections that can be iterated over, producing a sequence of Documents,
one document a time.

DocumentDestination subclasses represent collections that can receive Documents one document a time.
"""

from abc import ABC, abstractmethod

__pdoc__ = {
    "Corpus.__getitem__": True,
    "Corpus.__setitem__": True,
    "Corpus.__len__": True,
    "DocumentSource.__iter__": True,
}


class Corpus(ABC):
    @abstractmethod
    def __getitem__(self, idx: int):
        """
        A corpus object must allow getting an item by its idx, e.g. `mycorpus[2]`
        For each index, a corpus must either return a single Document or None.

        Args:
            idx: the index of the document

        Returns:
            a document or None

        Throws:
            exception if the index idx does not exist in the corpus
        """
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        """
        A corpus object must allow setting an item by its idx, e.g. `mycorpus[2] = doc`
        The item assigned must be a document or None.

        Args:
            idx: the index of the document
            value: a document or None

        Throws:
            exception if the index idx does not exist in the corpus
        """
        pass

    @abstractmethod
    def __len__(self):
        """
        Returns the size of the corpus.
        """
        pass


class DocumentSource(ABC):
    @abstractmethod
    def __iter__(self):
        return self

    @abstractmethod
    def __next__(self):
        pass


class DocumentDestination(ABC):
    @abstractmethod
    def append(self, doc):
        """
        A document destination must have the append method defined which is used to add a new document
        to the destination.

        Args:
            doc: the document to add
        """
