"""
Module that defines base classes for representing document collections.

Corpus classes represent collections with a fixed number of documents, where each document can be
accessed and stored by its index number, much like lists/arrays of documents.

DocumentSource classes represent collections that can be iterated over, producing a sequence of Documents,
one document a time.

DocumentDestination classes represent collections that can receive Documents one document a time.
"""

import random
from abc import ABC, abstractmethod
from typing import Iterable as TypingIterable
from typing import Iterator as TypingIterator
from typing import Sized
from typing import Union
from contextlib import AbstractContextManager
import numbers
from gatenlp.document import Document

__pdoc__ = {
    "Corpus.__getitem__": True,
    "Corpus.__setitem__": True,
    "Corpus.__len__": True,
    "DocumentSource.__iter__": True,
}


class CorpusSourceBase:
    """
    Common base trait for Corpus and Source classes. So far just provides methods to
    get nparts and partnr even for objects which are not sharded.
    """
    @property
    def nparts(self):
        """
        Return the total number of parts for an EveryNth corpus or document source.
        This is 1 for all other corpus/source instances.
        """
        return 1

    @property
    def partnr(self):
        """
        Return the part number for an EveryNth corpus or document source.
        This is 0 for all other corpus/source instances.
        """
        return 0


class MultiProcessingAble:
    """
    A document source/destination/corpus class where duplicate instances can be used by several
    processes on the same node in parallel.
    """
    pass


class DistributedProcessingAble(MultiProcessingAble):
    """
    A document source/destination/corpus class where duplicate instances can be used from several nodes in parallel.
    """
    pass


class Corpus(ABC, CorpusSourceBase, Sized):
    """
    A corpus represents a collection of documents with a fixed number of elements which can be read and written
    using an index number, e.g. `doc = corpus[2]` and `corpus[2] = doc`. For each index in the allowed range,
    the element is either a document or (for a few corpus implementations) None (indicating that no document
    is available for this index).

    The index is an int with range 0 to N-1 where N is the number of documents in the corpus.

    NOTE: for most corpus implementations, setting an index to None should not be allowed as this would
    not work with batching and the use of the `store` method to save documents back into the corpus.
    """

    @abstractmethod
    def __getitem__(self, idx: int) -> Document:
        """
        Retrieve a document from the corpus. Note that fetching a document from the corpus will usually set
        a special transient document feature that contains the index of the document so it can be
        stored back at the same index using the method `store()` later. If a corpus implementaton does not
        set that feature, batching and the use of the `store()` method to save back documents are not
        supported.

        Args:
            idx: the index of the document

        Returns:
            a document or None

        Throws:
            exception if the index idx does not exist in the corpus
        """
        pass

    @abstractmethod
    def __setitem__(self, idx: int, doc: Document) -> None:
        """
        A corpus object must allow setting an item by its idx, e.g. `mycorpus[2] = doc`
        The item assigned must be a document or (in rare cases) None.

        Args:
            idx: the index of the document
            doc: a document

        Throws:
            exception if the index idx does not exist in the corpus
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        """
        Returns the size of the corpus.
        """
        pass

    def idxfeatname(self) -> str:
        """
        Return the name of the transient feature to receive the index used to access a document
        from a corpus.
        """
        return "__idx_" + str(id(self))

    def setidxfeature(self, doc: Document, idx: int):
        """
        Sets the special transient feature of the document to the given index.

        Args:
            doc: the document
            idx: the index used to access the document in a corpus
        """
        if doc is not None:
            doc.features[self.idxfeatname()] = idx

    def store(self, doc: Document) -> None:
        """
        This method allows to store a document that comes from the same corpus back without the need to specify
        the index. This is useful for processing documents in batches or in streams. For this to work, all
        corpus implementations MUST make sure to store the index as part of returning a document with
        `__getitem__`. The index is stored in document feature `self.idxfeatname()`.

        Args:
            doc: the document to store back into the corpus, should be a document that was retrieved from the same
                 corpus or (in very rare cases and with specific corpus implementations only) None.
                 The default behaviour for None is to throw an exception, this must be overriden by
                 subclasses where store(None) should be supported.

        Raises:
            Exception: if the index is not stored in a document feature `self.idxfeatname()`
        """
        if doc is None:
            raise Exception("Cannot store back None into a corpus")
        assert isinstance(doc, Document)
        idx = doc.features.get(self.idxfeatname())
        if idx is None:
            raise Exception("Cannot store back document, no __idx_ID feature")
        self.__setitem__(idx, doc)

    def append(self, document: Document) -> int:
        """
        Some corpus implementations may provide the append method to allow for adding documents (i.e.
        use the corpus like a DocumentDestination).

        Important: this will probably not work properly in situations where another
        corpus wraps a corpus that allows appending. Use with care!

        Args:
            document: the document to add to the corpus or (in rare cases and for specific Corpus
                implementations) None.

        Returns:
            the index where the document was stored
        """
        raise RuntimeError("Corpus does not allow appending")


class DocumentSource(ABC, TypingIterable, CorpusSourceBase):
    """
    A document source is an iterable of documents which will generate an unknown number of documents.
    """
    def __iter__(self) -> TypingIterator[Document]:
        pass


# NOTE: AbstractContextManager already inherits from ABC, so no need to list as base class here!
class DocumentDestination(AbstractContextManager):
    """
    A document destination is something that accepts an a priori unknown number of documents via
    the append method.

    Document destinations all provide a `close()` method and must be closed after use.

    Document destinations can be used as context managers i.e. one can do
    `with SomeDocumentDest(..) as dest: dest.append(doc)` which will take care of closing the
    destination automatically.
    """

    @abstractmethod
    def append(self, doc: Document) -> None:
        """
        Append the given document to the destination.

        Args:
            doc: the document to add, if this is None, by default nothing is actually added to the destination,
                but specific implementations may change this behaviour.
        """
        pass

    def close(self) -> None:
        """
        Close the document destination. The default context manager implementation always calls
        close(), even when an exception is raised.
        """
        pass

    def __exit__(self, exctype, value, traceback) -> bool:
        """
        The default implementation always invokes close() and
        does not suppress any exception (always returns False)
        """
        self.close()
        return False   # do not suppress any exception


class StringIdCorpus:
    """
    A corpus which allows to use string ids in addition to integer indices for setting and getting documents.
    """
    # NOTE: the only thing that is really different is the type signature for some of the methods
    @abstractmethod
    def __getitem__(self, key: Union[int, str]) -> Document:
        """
        Retrieve a document from the corpus by either its numeric index or its string id.

        Args:
            key: the index of the document or the unique string id

        Returns:
            a document or None

        Throws:
            exception if the index idx does not exist in the corpus
        """
        pass

    @abstractmethod
    def __setitem__(self, idx: Union[int, str], doc: Document) -> None:
        """
        Store a document into the corpus by either its numeric index or its strign id.

        Args:
            idx: the index or the string id of the document
            doc: a document

        Throws:
            exception if the index idx does not exist in the corpus
        """
        pass


class EveryNthBase:
    """
    A Source or Corpus that wraps another Source or Corpus so that only every nth document, starting
    with some document 0 <= k < n is included.

    Such classes must provide the initialization keyword parameters partnr and nparts which may
    have default values of 0 and 1 for single part resources.
    """
    def __init__(self, nparts=1, partnr=0):
        self._nparts = nparts
        self._partnr = partnr

    @property
    def nparts(self):
        return self._nparts

    @property
    def partnr(self):
        return self._partnr


class EveryNthSource(EveryNthBase, DocumentSource):
    """
    A wrapper to make any DocumentSource that is multiprocessing or distributed processing-able
    viewable in parts.

    Wraps a document source to only return every nparts-th document, starting with the partnr-th document.
    For example with nparts=3 and partnr=0, the documents 0,1,2,3,4 correspond to the
    documents 0,3,6,9,12 of the wrapped dataset, with nparts=3 and partnr=2, we get
    documents 2,5,8,11,14 etc.
    """
    def __init__(self, source: DocumentSource, nparts: int = 1, partnr: int = 0):
        assert isinstance(source, DocumentSource)
        # this uses Integral so we can also support integral types from Numpy etc!
        if (not isinstance(nparts, numbers.Integral)) or (
            not isinstance(partnr, numbers.Integral)
        ):
            raise Exception("nparts and partnr must be integers.")
        super().__init__(nparts=nparts, partnr=partnr)
        self.source = source

        if nparts < 2 or partnr < 0 or partnr >= nparts:
            raise Exception("nparts must be >= 2 and partnr must be >= 0 and < nparts")
        self.source = source

    def __iter__(self) -> TypingIterator[Document]:
        for idx, doc in enumerate(self.source):
            if idx % self.nparts == self.partnr:
                yield doc


class EveryNthCorpus(EveryNthBase, Corpus):
    """
    A wrapper to make any corpus that is multiprocessing/distributedprocessing-able shardable.

    Wraps a corpus to only every nparts-th document, starting with the partnr-th document.
    For example with nparts=3 and partnr=0, the documents 0,1,2,3,4 correspond to the
    documents 0,3,6,9,12 of the wrapped dataset, with nparts=3 and partnr=2, we get
    documents 2,5,8,11,14 etc.

    This is useful to access a subset of documents from a corpus from different concurrent
    processes (the wrapped corpus must be MultiProcessingAble for that!).
    """
    def __init__(self, corpus: Corpus, nparts: int = 1, partnr: int = 0):
        assert isinstance(corpus, Corpus)
        # this uses Integral so we can also support integral types from Numpy etc!
        if (not isinstance(nparts, numbers.Integral)) or (
            not isinstance(partnr, numbers.Integral)
        ):
            raise Exception("nparts and partnr must be integers.")
        if nparts < 2 or partnr < 0 or partnr >= nparts:
            raise Exception("nparts must be >= 2 and partnr must be >= 0 and < nparts")
        super().__init__(nparts=nparts, partnr=partnr)
        self.corpus = corpus

    def __len__(self):
        olen = len(self.corpus)
        # alternate way to calculate?
        # int((olen + (self.nparts - self.partnr) - 1) / self.partnr)
        return int(olen/self.nparts) + (1 if (olen % self.nparts) > self.partnr else 0)

    def _orig_idx(self, idx: int) -> int:
        return idx * self.nparts + self.partnr

    def __getitem__(self, idx: int) -> Document:
        # NOTE: we do not store the index in a feature for this wrapper as the wrapped
        # corpus index is eventually the only one that matters
        return self.corpus[self._orig_idx(idx)]

    def __setitem__(self, idx: int, doc: Document) -> None:
        self.corpus[self._orig_idx(idx)] = doc

    def store(self, doc: Document) -> None:
        # stored using the feature from the original index!
        self.corpus.store(doc)

    def append(self, document: Document) -> int:
        raise Exception("Method append not supported for EveryNthCorpus")


class ShuffledCorpus(Corpus):
    """
    Wraps a corpus to reorder the documents in the corpus randomly.
    """

    def __init__(self, corpus, seed=None):
        """
        Create a ShuffledCorpus wrapper.

        Args:
            seed: if an integer and > 0, shuffle the list of instances randomly, using the given seed.
                If the seed is 0, the RNGs random random seed is used, if seed is -1, the seed is not set at all
                and whatever the current state of the random generator is is used. If None, no shuffling is
                carried out. If this is None or not an integer, same as 0.
        """
        super().__init__()
        self.corpus = corpus
        self.seed = seed
        self.idxs = list(range(len(corpus)))
        self.shuffle(seed)

    def shuffle(self, seed=0):
        """
        Shuffle instance list order,
        :param seed: random seed to set, if seed is 0, a random random seed is used, if -1, seed is not set.
        If seed is None, no shuffling is carried out.
        :return:
        """
        if isinstance(seed, numbers.Integral):  # also allow for np.int8(n) and the like
            if seed != -1:
                if seed == 0:
                    random.seed()
                else:
                    random.seed(seed)
            random.shuffle(self.idxs)
        else:  # not an integer seed: None or some other type
            # same as seed 0
            random.seed()
            random.shuffle(self.idxs)

    def __getitem__(self, idx):
        doc = self.corpus[self.idxs[idx]]
        self.setidxfeature(doc, idx)
        return self.corpus[self.idxs[idx]]

    def __setitem__(self, idx, doc):
        if not isinstance(idx, numbers.Integral):
            raise Exception("Item must be an integer")
        if idx >= len(self.idxs) or idx < 0:
            raise Exception("Index idx must be >= 0 and < {}".format(len(self)))
        # the index to access in the original dataset is int(n*item)+k
        self.corpus[self.idxs[idx]] = doc

    def __len__(self):
        return len(self.idxs)

    def append(self, document: Document) -> int:
        raise Exception("Method append not supported for ShuffledCorpus")


class CachedCorpus(Corpus):
    """
    Wraps two other corpora: the base corpus which may be slow to access, may not be writable etc. and the
    cache corpus which is meant to be fast. The cache corpus may initially contain only None elements or no
    files. This wrapper caches documents when they are written to, but this can be changed to caching on read.
    """

    def __init__(self, basecorpus, cachecorpus, cacheonread=False):
        """
        TODO: this is still work in progress!

        Creates a cached corpus.
        This accesses data from the cachecorpus, if it does not exist in there (entry is,
        None) will instead fall back to the base corpus.

        This cached corpus can be set up to cache on read or cache on write.

        Args:
            basecorpus: any corpus
            cachecorpus: any corpus that can return None for non-existing elements, e.g. a NumberedDirFilesCorpus
              or just an in-memory list or array.
            cacheonread: if True, writes to the cache as soon as an item has been read from the base dataset.
                Otherwise will only write to the cache dataset when an item is set. This allows to cache the result
                of processing efficiently.
        """
        assert len(cachecorpus) == len(basecorpus)
        self.basecorpus = basecorpus
        self.cachecorpus = cachecorpus
        self.cacheonread = cacheonread

    def __len__(self):
        return len(self.basecorpus)

    def __getitem__(self, index):
        tmp = self.cachecorpus[index]
        if tmp is None:
            tmp = self.basecorpus[index]
            if self.cacheonread:
                self.basecorpus[index] = tmp
        self.setidxfeature(tmp, index)
        return tmp

    def __setitem__(self, index, value):
        self.cachecorpus[index] = value
