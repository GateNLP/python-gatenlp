"""
Module that defines base and implementation classes for representing document collections.

Corpus subclasses represent collections with a fixed number of documents, where each document can be
accessed and stored by its index number, much like lists/arrays of documents.

DocumentSource subclasses represent collections that can be iterated over, producing a sequence of Documents,
one document a time.

DocumentDestination subclasses represent collections that can receive Documents one document a time.
"""

import os
import random
from abc import ABC, abstractmethod
import numbers
from gatenlp.serialization.default import read_lines_from
from gatenlp.document import Document

__pdoc__ = {
    "Corpus.__getitem__": True,
    "Corpus.__setitem__": True,
    "Corpus.__len__": True,
    "DocumentSource.__iter__": True,
}


class Corpus(ABC):
    """
    A corpus represents a collection of documents with a fixed number of elements which can be read and written
    using an index number, e.g. `doc = corpus[2]` and `corpus[2] = doc`. For each index in the allowed range,
    the element is either a document or None.

    NOTE: assigning None to a corpus removes the element from the corpus.

    """

    @abstractmethod
    def __getitem__(self, idx: int):
        """
        Retrieve a document from the corpus.

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
            key: the index of the document
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


class DocumentDestination(ABC):
    @abstractmethod
    def append(self, doc):
        """
        A document destination must have the append method defined which is used to add a new document
        to the destination.

        Args:
            doc: the document to add
        """
        pass

    def close(self):
        """
        Must have a close method that is used to end writing and close the destination.
        """
        pass


class JsonLinesFileSource(DocumentSource):
    """
    A document source which reads one json serialization of a document from each line of the given file.
    """

    def __init__(self, file):
        """
        Create a JsonLinesFileSource.

        Args:
            file: the file path (a string) or an open file handle.
        """
        self.file = file

    def __iter__(self):
        with open(self.file, "rt", encoding="utf-8") as infp:
            for line in infp:
                yield Document.load_mem(line, fmt="json")


class JsonLinesFileDestination(DocumentDestination):
    """
    Writes one line of JSON per document to the a single output file.
    """

    def __init__(self, file):
        """

        Args:
            file: the file to write to. If it exsits, it gets overwritten without warning.
               Expected to be a string or an open file handle.
        """
        if isinstance(file, str):
            self.fh = open(file, "wt", encoding="utf-8")
        else:
            self.fh = file
        self.n = 0

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.fh.close()

    def append(self, doc):
        """
        Append a document to the destination.

        Args:
            doc: the document
        """
        self.fh.write(doc.save_mem(fmt="json"))
        self.fh.write("\n")
        self.n += 1

    def close(self):
        self.fh.close()


def matching_paths(dirpath, exts=None, recursive=True, relative=True):
    """
    Yields all relative file paths from dirpath which match the list of extensions
    and which do not start with a dot.

    Args:
        dirpath: the directory to traverse
        exts: a list of allowed extensions (inluding the dot)
        recursive: if True (default) include all matching paths from all subdirectories as well, otherwise
          only paths from the top directory.
        relative: if True (default), the paths are relative to the directory path
    """
    if recursive:
        for root, dirnames, filenames in os.walk(dirpath):
            for fname in filenames:
                if exts:
                    for ext in exts:
                        if fname.endswith(ext) and not fname.startswith("."):
                            if relative:
                                yield os.path.relpath(
                                    os.path.join(root, fname), dirpath
                                )
                            else:
                                yield os.path.join(root, fname)
                            break
                else:
                    if not fname.startswith("."):
                        if relative:
                            yield os.path.relpath(os.path.join(root, fname), dirpath)
                        else:
                            yield os.path.join(root, fname)
    else:
        for fname in os.listdir(dirpath):
            full = os.path.join(dirpath, fname)
            if not os.path.isfile(full) or fname.startswith("."):
                pass
            elif exts:
                for ext in exts:
                    if fname.endswith(ext):
                        if relative:
                            yield os.path.relpath(full, dirpath)
                        else:
                            yield full
                        break
            else:
                if relative:
                    yield os.path.relpath(full, dirpath)
                else:
                    yield full


def make_file_path_fromidx(digits=1, levels=1):
    """
    Creates a method that returns a file path for the given number of leading digits and levels.

    Args:
        digits: minimum number of digits to use for the path, any number with less digits will have leading zeros
           added.
        levels: how to split the original sequence of digits into a hierarchical path name. For example if digits=10
           and levels=3, the generated function will convert the index number 23 into 0/000/000/023

    Returns:
        a function that takes doc and idx and return a path name (str)
    """
    if (
        not isinstance(digits, int)
        or not isinstance(levels, int)
        or digits < 1
        or levels < 1
        or digits < levels
    ):
        raise Exception(
            f"digits and levels must be integers larger than 0 and digits must not be smaller than levels, got {digits}/{levels}"
        )

    def file_path_fromidx(doc=None, idx=None):
        if idx is None or not isinstance(idx, int) or idx < 0:
            raise Exception("Index must be an integer >= 0")
        per = int(digits / levels)
        asstr = str(idx)
        digs = max(0, digits - len(asstr))
        tmp = "0" * digs
        tmp += str(idx)
        path = ""
        fromdigit = len(tmp) - per
        todigit = len(tmp)
        for lvl in range(levels - 1):
            path = tmp[fromdigit:todigit] + path
            # print("per=", per, "from=", fromdigit, "to=", todigit, "sec=", tmp[fromdigit:todigit])
            path = "/" + path
            fromdigit = fromdigit - per
            todigit = todigit - per
        path = tmp[:todigit] + path
        return path

    return file_path_fromidx


def debug_maker(var1=22):
    def debug_closure():
        print(var1)

    return debug_closure


class DirFilesSource(DocumentSource):
    def __init__(
        self,
        dirpath,
        paths=None,
        paths_from=None,
        exts=None,
        fmt=None,
        recursive=True,
        sort=False,
        every_n=1,
        every_n_k=0,
    ):
        """
        Create a DirFilesSource.

        Args:
            dirpath: the directory that contains the file to load as documents.
            paths:  if not None, must be an iterable of relate file paths to load from the directory
            paths_from: if not None, must be a file or URL to load a list of file paths from
            exts: an iterable of allowed file extensions or file extension regexps
            fmt: the format to use for loading files. This is only useful if all files have the same format
               but the file extensions does not indicate the format.
            recursive: recursively include paths from all subdirectories as well
            sort: sort paths so they get processed in sort order. The paths get always sorted if every_n is > 1.
            every_n: only yield every nth document (default 1: every document)
            every_n_k: start with that index, before yielding every_n th document (default 0: start at beginning)
        """
        self.dirpath = dirpath
        if paths is not None and paths_from is not None:
            raise Exception("Parameters paths and paths_from cannot be both specified")
        if paths is not None:
            self.paths = paths
        elif paths_from is not None:
            self.paths = []
            for p in read_lines_from(paths_from):
                self.paths.append(p.rstrip("\n\r"))
        else:
            self.paths = list(matching_paths(dirpath, exts=exts, recursive=recursive))
        if sort or every_n > 1:
            self.paths.sort()
        if every_n > 1:
            self.paths = [
                p
                for idx, p in enumerate(self.paths)
                if ((idx - every_n_k) % every_n) == 0
            ]
        self.every_n = every_n
        self.every_n_k = every_n_k
        self.fmt = fmt

    def __iter__(self):
        """
        Yield the next document from the source.
        """
        for p in self.paths:
            yield Document.load(os.path.join(self.dirpath, p), fmt=self.fmt)


class DirFilesDestination(DocumentDestination):
    """
    A destination where each document is stored in a file in a directory or directory tree in some
    known serialization format. The filename or path of the file can be derived from a document feature,
    the document name, the running number of file added, or any function that can derive a file path
    from the document and the running number.


    """

    def __init__(self, dirpath, path_from="idx", ext="bdocjs", fmt=None):
        """
        Create a destination to store documents in files inside a directory or directory tree.

        Args:
            dirpath: the directory to contain the files
            path_from: one of options listed below. If a string is used as a path name, then the forward slash
                 is always used as the directory path separator, on all systems!
               * "idx": just use the index/running number of the added document as the base name
               * "idx:5": use the index/running number with at least 5 digits in the name.
               * "idx:10:2": use the index and organize a total of 10 digits into a hierarchical
                   pathname of 2 levels, so 10:2 would mean the first 5 digits are for the name of the subdirectory
                   and the second 5 digits are for the file base name. 10:3 would have for levels, the first
                   subdirectory level with 1 digit, the next two with 3 digits and the remaining 3 digits for the
                   filename.
                   NOTE: "idx" by itself is equivalent to idx:1:1
                * "feature:fname": use the document feature with the feature name fname as a relative path as is
                   but add the extension
                * "name": use the document name as the relative path, but add extension.
                * somefunction: a function that should return the pathname (without extension) and should take two
                   keyword arguments: doc (the document) and idx (the running index of the document).
            ext: the file extension to add to all generated file names
            fmt: the format to use for serializing the document, if None, will try to determine from the extension.
        """
        if not os.path.isdir(dirpath):
            raise Exception("Not a directory: ", dirpath)
        self.dirpath = dirpath
        self.idx = 0
        if path_from.startswith("idx"):
            rest = path_from[
                3:
            ]  # if we have digits or levels, there is a leading colon!
            if len(rest) == 0:
                digits = 1
                levels = 1
            else:
                parms = rest.split(":")
                parms.append(1)
                digits, levels = parms[1:3]
                digits = int(digits)
                levels = int(levels)
            self.file_path_maker = make_file_path_fromidx(digits, levels)
        elif path_from.startswith("feature"):
            _, fname = path_from.split(":")
            self.file_path_maker = lambda doc: doc.features[fname]
        elif path_from == "name":
            self.file_path_maker = lambda doc: doc.name
        elif callable(path_from):
            self.file_path_maker = path_from
        else:
            raise Exception(f"Not allowed for path_from: {path_from}")
        if not ext.startswith("."):
            ext = "." + ext
        self.ext = ext
        self.fmt = fmt

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        pass

    def append(self, doc):
        path = self.file_path_maker(doc=doc, idx=self.idx)
        path = os.path.normpath(
            path
        )  # convert forward slashes to backslashes on windows
        path = os.path.join(self.dirpath, path) + self.ext
        # check if we need to create the directories. For this we first need to get the directories part of the path,
        # which is everything left of the last slash
        if os.path.sep in path:
            dirs = path[: path.rindex(os.path.sep)]
            if not os.path.exists(os.path.normpath(dirs)):
                os.makedirs(dirs)
        Document.save(doc, path, fmt=self.fmt)
        self.idx += 1

    def close(self):
        pass


class DirFilesCorpus(Corpus):
    """
    A corpus representing all files in a directory that match the given extension.
    """

    def __init__(self, dirpath, ext="bdocjs", fmt=None, recursive=True):
        """
        Creates the DirCorpus.

        Args:
            dirpath: the directory path
            ext: the file extension that must be matched by all files for the corpus
            fmt: the format to use, if None, will be determined from the extension
            recursive: if True (default) all matching files from all subdirectories are included
        """
        if not ext.startswith("."):
            ext = "." + ext
        self.dirpath = dirpath
        self.ext = ext
        self.fmt = fmt
        self.paths = list(matching_paths(dirpath, exts=[ext], recursive=recursive))
        self.size = len(self.paths)
        pass

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        assert isinstance(idx, int)
        path = self.paths[idx]
        doc = Document.load(os.path.join(self.dirpath, path), fmt=self.fmt)
        return doc

    def __setitem__(self, idx, doc):
        assert isinstance(idx, int)
        assert isinstance(doc, Document)
        path = self.paths[idx]
        doc.save(os.path.join(self.dirpath, path), fmt=self.fmt)


class NumberedDirFilesCorpus:
    """
    A corpus that represents files from a (nested) directory, where the filename is derived from
    the index number of the document. This corpus can represent missing elements as None, both
    on reading (when the corresponding expected document does not exist) and on writing (the
    corresponding document gets deleted).
    """

    def __init__(self, dirpath, digits=1, levels=1, ext="bdocjs", fmt=None, size=None):
        """
        Creates the DirCorpus.

        Args:
            dirpath: the directory path
            digits: the number of digits to use for the file path
            levels: the number of levels to split the digits up which are then used as subdire names.
            ext: the file extension used for all files in the corpus
            fmt: the format to use, if None, determined from the extension
            size: the size of the corpus. This can be used to create a corpus from an empty directory
              to contain only None elements initially.  It can also be used to limit access to only the
              first size elements if the directory contains more documents.
        """
        if not ext.startswith("."):
            ext = "." + ext
        self.dirpath = dirpath
        self.ext = ext
        self.fmt = fmt
        self.size = size
        self.file_path_maker = make_file_path_fromidx(digits, levels)
        pass

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        assert isinstance(idx, int)
        path = self.file_path_maker(idx)
        path = path + self.ext
        if os.path.exists(path):
            doc = Document.load(os.path.join(self.dirpath, path), fmt=self.fmt)
        else:
            doc = None
        return doc

    def __setitem__(self, idx, doc):
        assert isinstance(idx, int)
        assert doc is None or isinstance(doc, Document)
        path = self.file_path_maker(idx)
        path = path + self.ext
        if doc is None:
            if os.path.exists(path):
                os.remove(path)
        else:
            doc = Document.save(os.path.join(self.dirpath, path), fmt=self.fmt)


class TsvFileSource(DocumentSource):
    """
    A TsvFileSource is a DocumentSource which is a single TSV file with a fixed number of tab-separated
    values per row. Each document in sequence is created from the text in one of the columns and
    document features can be set from arbitrary columns as well.
    """

    def __init__(self, source, hdr=True, text_col=None, feature_cols=None):
        """
        Creates the TsvFileSource.

        Args:
            source: a file path or URL
            hdr: if True (default), expects a header line with the column names, if a list, should be the list
              of column names, if False/None, no header line is expected.
            text_col: the column which contains the text for creating the document. Either the column number,
              or the name of the column (only possible if there is a header line) or a function that should
              take the list of fields and arbitrary kwargs and return the text. Also passes "cols" and "n"
              as keyward arguments.
            feature_cols: if not None, must be a dictionary mapping document feature names to the column numbers or
              column names of where to get the feature value from of a function that should take the list of fields
              and arbitrary kwargs and return a dictionary with the features. Also passes "cols" (dict
              mapping column names to column indices, or None) and "n" (current line number) as keyword arguments.
        """
        assert text_col is not None
        self.hdr = hdr
        self.text_col = text_col
        self.feature_cols = feature_cols
        self.source = source
        self.n = 0
        self.hdr2col = {}

    def __iter__(self):
        reader = read_lines_from(self.source)
        if self.hdr == True and self.n == 0:
            self.n += 1
            self.hdr = next(reader).rstrip("\n\r").split("\t")
        if self.hdr:
            self.hdr2col = {name: idx for idx, name in enumerate(self.hdr)}
        for line in reader:
            fields = line.split("\t")
            if isinstance(self.text_col, int):
                text = fields[self.text_col]
            elif callable(self.text_col):
                text = self.text_col(fields, cols=self.hdr2col, n=self.n)
            else:
                text = fields[self.hdr2col[self.text_col]]
            doc = Document(text)
            if self.feature_cols:
                if callable(self.feature_cols):
                    doc.features.update(
                        self.feature_cols(fields, cols=self.hdr2col, n=self.n)
                    )
                else:
                    for fname, colid in self.feature_cols.items():
                        if isinstance(colid, int):
                            value = fields[colid]
                        else:
                            value = fields[self.hdr2col[colid]]
                    doc.features[fname] = value
            self.n += 1
            yield doc


class PandasDfSource(DocumentSource):
    """
    A document source which creates documents from the text in some data frame column for each row, and
    sets features from arbitrary columns in the row.
    """

    def __init__(self, df, text_col=None, feature_cols=None):
        """
        Creates a PandasDfSource.

        Args:
            df: the data frae
            text_col:  the name of the column that contains the text
            feature_cols: a dictionary that maps document feature names to column names of where to get the
               feature value from (default: None)
        """
        assert text_col is not None
        self.text_col = text_col
        self.feature_cols = feature_cols
        self.source = df
        self.reader = df.iterrows()
        self.n = 0

    def __iter__(self):
        for _, row in self.reader:
            text = row[self.text_col]
            doc = Document(text)
            if self.feature_cols:
                for fname, colname in self.feature_cols.items():
                    value = row[colname]
                    doc.features[fname] = value
            self.n += 1
            yield doc


class EveryNthCorpus(Corpus):
    """
    Wraps a corpus to only every nth document, starting with the kth document.
    For example with n=3 and k=0, the documents 0,1,2,3,4 correspond to the
    documents 0,3,6,9,12 of the wrapped dataset, with n=3 and k=2, we get
    documents 2,5,8,11,14 etc.

    This is useful to access a subset of documents from a corpus from n different concurrent
    processes (in that case, the wrapped corpus must allow concurrent access!) or
    split a corpus into n subsets for other purposes.

    """

    def __init__(self, corpus, every_n, every_n_k):
        """
        Create an EveryNthCorpus.

        Args:
            corpus: the corpus to wrap, must allow multiple concurrent access
            every_n: the increment
            every_n_k: the offset, must be < n
        """
        super().__init__()
        if (not isinstance(every_n, numbers.Integral)) or (
            not isinstance(every_n_k, numbers.Integral)
        ):
            raise Exception("n and k must be integers.")
        if every_n < 2 or every_n_k < 0 or every_n_k >= every_n:
            raise Exception("n must be >= 2 and k must be >= 0 and < n")
        self.every_n = every_n
        self.every_n_k = every_n_k
        self.corpus = corpus
        # precalculate the length
        otherlen = len(corpus)
        # the size of this dataset is int((otherlen + (n-k) - 1)/k)
        self.len = int((otherlen + (every_n - every_n_k) - 1) / every_n_k)

    def __getitem__(self, idx):
        if not isinstance(idx, numbers.Integral):
            raise Exception("Item must be an integer")
        if idx >= self.len or idx < 0:
            raise Exception("Index idx must be >= 0 and < {}".format(self.len))
        # the index to access in the original dataset is int(n*item)+k
        return self.corpus[idx * self.every_n + self.every_n_k]

    def __setitem__(self, idx, doc):
        if not isinstance(idx, numbers.Integral):
            raise Exception("Item must be an integer")
        if idx >= self.len or idx < 0:
            raise Exception("Index idx must be >= 0 and < {}".format(self.len))
        # the index to access in the original dataset is int(n*item)+k
        self.corpus[idx * self.every_n + self.every_n_k] = doc

    def __len__(self):
        return self.len


class EveryNthSource(DocumentSource):
    """
    Wraps a document source to only return every nth document, starting with the kth document.
    For example with n=3 and k=0, the documents 0,1,2,3,4 correspond to the
    documents 0,3,6,9,12 of the wrapped dataset, with n=3 and k=2, we get
    documents 2,5,8,11,14 etc. The wrapped corpus must allow to get used by more than
    one client at the same time!
    """

    def __init__(self, source, every_n, every_n_k):
        """
        Create an EveryNthSource.

        Args:
            corpus: the corpus to wrap, must allow multiple concurrent access
            every_n: the increment
            every_n_k: the offset, must be < n
        """
        super().__init__()
        if (not isinstance(every_n, numbers.Integral)) or (
            not isinstance(every_n_k, numbers.Integral)
        ):
            raise Exception("n and k must be integers.")
        if every_n < 2 or every_n_k < 0 or every_n_k >= every_n:
            raise Exception("n must be >= 2 and k must be >= 0 and < n")
        self.every_n = every_n
        self.every_n_k = every_n_k
        self.source = source

    def __iter__(self):
        idx = 0
        for doc in self.source:
            if (idx - self.every_n_k) % self.every_n == 0:
                yield doc


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
        return self.corpus[self.idxs[idx]]

    def __setitem__(self, idx, doc):
        # TODO: refactor into separate utility function
        if not isinstance(idx, numbers.Integral):
            raise Exception("Item must be an integer")
        if idx >= self.len or idx < 0:
            raise Exception("Index idx must be >= 0 and < {}".format(self.len))
        # the index to access in the original dataset is int(n*item)+k
        self.corpus[self.idxs[idx]] = doc

    def __len__(self):
        return len(self.idxs)


class CachedCorpus(Corpus):
    """
    Wraps two other corpora: the base corpus which may be slow to access, may not be writable etc. and the
    cache corpus which is meant to be fast. The cache corpus may initially contain only None elements or no
    files. This wrapper caches documents when they are written to, but this can be changed to caching on read.
    """

    def __init__(self, basecorpus, cachecorpus, cacheonread=False):
        """
        Creates a cached corpus.
        This accesses data from the cachecorpus, if it does not exist in there (entry is,
        None) will instead fall back to the base corpus.

        This cached corpus can be set up to cache on read or cache on write.

        Args:
            basedataset: any corpus
            cachedataset: any corpus that can return None for non-existing elements, e.g. a NumberedDirFilesCorpus
              or just an in-memory list or array.
            cacheonread: if True, writes to the cache as soon as an item has been read from the base dataset.
                Otherwise will only write to the cache dataset when an item is set. This allows to cache the result
                of processing efficiently.
        """
        assert len(cachecorpus) == len(basecorpus)
        self.is_writable = True
        self.basecorpus = basecorpus
        self.cachecorpus = cachecorpus
        self.cacheonread = cacheonread

    def __len__(self):
        return len(self.basecorpus)

    def __getitem__(self, index):
        tmp = self.cachecorpus[index]
        if tmp is None:
            tmp = self.basecorpus
            if self.cacheonread:
                self[index] = tmp
        return tmp

    def __setitem__(self, index, value):
        self.cachecorpus[index] = value
