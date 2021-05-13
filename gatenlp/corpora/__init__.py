"""
Module that defines base and implementation classes for representing document collections.

Corpus subclasses represent collections with a fixed number of documents, where each document can be
accessed and stored by its index number, much like lists/arrays of documents.

DocumentSource subclasses represent collections that can be iterated over, producing a sequence of Documents,
one document a time.

DocumentDestination subclasses represent collections that can receive Documents one document a time.
"""

from gatenlp.corpora.base import Corpus, DocumentSource, DocumentDestination
from gatenlp.corpora.base import MultiProcessingAble, DistributedProcessingAble
from gatenlp.corpora.base import EveryNthCorpus, EveryNthSource, ShuffledCorpus, CachedCorpus
from gatenlp.corpora.memory import ListCorpus, PandasDfSource
from gatenlp.corpora.files import BdocjsLinesFileSource, BdocjsLinesFileDestination
from gatenlp.corpora.files import JsonLinesFileSource, JsonLinesFileDestination
from gatenlp.corpora.files import TsvFileSource
from gatenlp.corpora.dirs import DirFilesCorpus, DirFilesSource, DirFilesDestination, NumberedDirFilesCorpus