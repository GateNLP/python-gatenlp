"""
Module that defines base and implementation classes for representing document collections.

Corpus subclasses represent collections with a fixed number of documents, where each document can be
accessed and stored by its index number, much like lists/arrays of documents.

DocumentSource subclasses represent collections that can be iterated over, producing a sequence of Documents,
one document a time.

DocumentDestination subclasses represent collections that can receive Documents one document a time.
"""

import os
from abc import ABC, abstractmethod
from gatenlp.serialization.default import read_lines_from
from gatenlp.document import  Document

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
        self.fh = open(file, "rt", encoding="utf-8")

    def __iter__(self):
        return self

    def __next__(self):
        line = self.fh.readline()
        doc = Document.load_mem(line, fmt="json")
        return doc


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

    def append(self, doc):
        """
        Append a document to the destination.

        Args:
            doc: the document
        """
        self.fh.write(doc.save_mem(fmt="json"))
        self.fh.write("\n")
        self.n += 1


def matching_paths(dirpath, exts=None, recursive=True, relative=True):
    """
    Yields all relative file paths from dirpath which match the list of extensions
    and which do not start with a dot.

    Args:
        dir: the directory to traverse
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
                                yield os.path.relpath(dirpath, os.path.join(dirpath, fname))
                            else:
                                yield os.path.join(dirpath, fname)
                            break
                else:
                    if not fname.startswith("."):
                        if relative:
                            yield os.path.relpath(dirpath, os.path.join(dirpath, fname))
                        else:
                            os.path.join(dirpath, fname)
    else:
        for fname in os.listdir(dirpath):
            full = os.path.join(dirpath, fname)
            if not os.path.isfile(full) or fname.startswith("."):
                continue
            elif exts:
                for ext in exts:
                    if fname.endswith(ext):
                        if relative:
                            yield os.path.relpath(dirpath, full)
                        else:
                            yield full
                        break
            else:
                if relative:
                    yield os.path.relpath(dirpath, full)
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
    if not isinstance(digits, int) or isinstance(levels, int) or digits < 1 or levels < 1 or digits < levels:
        raise Exception("digits and levels must be integers larger than 0 and digits must not be smaller than levels")

    def file_path_fromidx(doc=None, idx=None, digits=10, levels=3):
        if idx is None or not isinstance(idx, int) or idx < 0:
            raise Exception("Index must be an integer >= 0")
        per = int(digits/levels)
        asstr = str(idx)
        digits = max(0, digits-len(asstr))
        tmp = "0" * digits
        tmp += str(idx)
        print("tmp=", tmp)
        path = ""
        fromdigit = len(tmp) - per
        todigit = len(tmp)
        for lvl in range(levels-1):
            path = tmp[fromdigit:todigit] + path
            print("per=", per, "from=", fromdigit, "to=", todigit, "sec=", tmp[fromdigit:todigit])
            path = "/" + path
            fromdigit = fromdigit - per
            todigit = todigit - per
        path = tmp[:todigit] + path
        path = os.path.normpath(path)  # convert forward slashes to backslashes on windows
        return path
    return file_path_fromidx


class DirFilesSource(DocumentSource):

    def __init__(self, dirpath, paths=None, paths_from=None, exts=None, fmt=None, recursive=True):
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
        self.fmt = fmt

    def __iter__(self):
        return self

    def __next__(self):
        """
        Yield the next document from the source.
        """
        for p in self.paths:
            Document.load(os.path.join(self.dirpath, p), fmt=self.fmt)


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
            rest = path_from[3:]
            if len(rest) == 0:
                digits = 1
                levels = 1
            else:
                parms = rest.split(":")
                parms.append(1)
                digits, levels = parms[0:2]
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

    def append(self, doc):
        path = self.file_path_maker(doc=doc, idx=self.idx)
        path = path + self.ext
        Document.save(os.path.join(self.dirpath, path), fmt=self.fmt)
        self.idx += 1


class DirCorpus(Corpus):
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
        self.paths = matching_paths(dirpath, exts=[ext], recursive=recursive)
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
              or the name of the column (only possible if there is a header line)
            feature_cols: if not None, must be a dictionary mapping document feature names to the column numbers or
              column names of where to get the feature value from.
        """
        self.hdr = hdr
        self.text_col = text_col
        self.feature_cols = feature_cols
        self.source = source
        self.reader = read_lines_from(source)
        self.n = 0
        self.hdr2col = {}

    def __iter__(self):
        return self

    def __next__(self):
        if self.hdr == True and self.n == 0:
            self.n += 1
            self.hdr = next(self.reader).split("\t")
        if self.hdr:
            self.hdr2col = {name: idx for idx, name in self.hdr}
        for line in self.reader:
            fields = line.split("\t")
            if isinstance(self.text_col, int):
                text = fields[self.text_col]
            else:
                text = fields[self.hdr2col[self.text_col]]
            doc = Document(text)
            if self.feature_cols:
                for k,v in self.feature_cols:
                    if isinstance(v, int):
                        value = fields[v]
                    else:
                        value = fields[self.hdr2col[v]]
                    doc.features[k] = value
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
        return self

    def __next__(self):
        for idx, row in self.reader:
            text = row[self.text_col]
            doc = Document(text)
            if self.feature_cols:
                for k,v in self.feature_cols:
                    value = row[v]
                    doc.features[k] = value
            self.n += 1
            yield doc

