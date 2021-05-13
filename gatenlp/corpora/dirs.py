"""
Module that defines Corpus and DocumentSource/DocumentDestination classes which access documents
as files in a directory.
"""

import os
from gatenlp.urlfileutils import yield_lines_from
from gatenlp.document import Document
from gatenlp.corpora.base import DocumentSource, DocumentDestination, Corpus
from gatenlp.corpora.base import MultiProcessingAble
from gatenlp.corpora.base import EveryNthBase


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
        for root, _, filenames in os.walk(dirpath):
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


def maker_file_path_fromidx(digits=1, levels=1):
    """
    Creates a method that returns a file path for the given number of leading digits and levels.

    Args:
        digits: minimum number of digits to use for the path, any number with less digits will have leading zeros
           added.
        levels: how to split the original sequence of digits into a hierarchical path name. For example if digits=10
           and levels=3, the generated function will convert the index number 23 into 0/000/000/023

    Returns:
        a function that takes the keyword arguments idx and doc and returns a relative path name (str)
    """
    if (
        not isinstance(digits, int)
        or not isinstance(levels, int)
        or digits < 1
        or levels < 1
        or digits < levels
    ):
        raise Exception(
            "digits and levels must be integers larger than 0 and digits must not be smaller than "
            f"levels, got {digits}/{levels}"
        )

    def file_path_fromidx(doc=None, idx=None):
        # NOTE: doc is unused here but used with other methods to create the file path!
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
        for _lvl in range(levels - 1):
            path = tmp[fromdigit:todigit] + path
            # print("per=", per, "from=", fromdigit, "to=", todigit, "sec=", tmp[fromdigit:todigit])
            path = "/" + path
            fromdigit = fromdigit - per
            todigit = todigit - per
        path = tmp[:todigit] + path
        return path

    return file_path_fromidx


# TODO: set the special features for the relative path, index number, document id?
class DirFilesSource(DocumentSource, EveryNthBase, MultiProcessingAble):
    """
    A document source which iterates over documents represented as files in a directory.
    """
    def __init__(
        self,
        dirpath,
        paths=None,
        paths_from=None,
        exts=None,
        fmt=None,
        recursive=True,
        sort=False,
        nparts=1,
        partnr=0,
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
            nshards: only yield every nshards-th document (default 1: every document)
            shardnr: start with that index, before yieldieng every nshards-th document (default 0: start at beginning)
        """
        self.dirpath = dirpath
        if paths is not None and paths_from is not None:
            raise Exception("Parameters paths and paths_from cannot be both specified")
        super().__init__(nparts=nparts, partnr=partnr)
        if paths is not None:
            self.paths = paths
        elif paths_from is not None:
            self.paths = []
            for pth in yield_lines_from(paths_from):
                self.paths.append(pth.rstrip("\n\r"))
        else:
            self.paths = list(matching_paths(dirpath, exts=exts, recursive=recursive))
        if sort or nparts > 1:
            self.paths.sort()
        if nparts > 1:
            self.paths = [
                p
                for idx, p in enumerate(self.paths)
                if ((idx - partnr) % nparts) == 0
            ]
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
            self.file_path_maker = maker_file_path_fromidx(digits, levels)
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
        """
        Add a document to the destination.

        Args:
            doc: the document or None, if None, no action is performed.
        """
        if doc is None:
            return
        assert isinstance(doc, Document)
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


class DirFilesCorpus(Corpus, MultiProcessingAble):
    """
    A corpus representing all files in a directory that match the given extension.
    """

    def __init__(self, dirpath, ext="bdocjs", fmt=None, recursive=True, sort=False, sort_reverse=False):
        """
        Creates the DirCorpus.

        Args:
            dirpath: the directory path
            ext: the file extension that must be matched by all files for the corpus
            fmt: the format to use, if None, will be determined from the extension
            recursive: if True (default) all matching files from all subdirectories are included
            sort: if True, sort by file paths, if a function sort by that function (default: False)
            sort_reverse: if sort is not False and this is True, sort in reverse order
        """
        if not ext.startswith("."):
            ext = "." + ext
        self.dirpath = dirpath
        self.ext = ext
        self.fmt = fmt
        self.paths = list(matching_paths(dirpath, exts=[ext], recursive=recursive))
        if sort:
            if callable(sort):
                self.paths.sort(key=sort, reverse=sort_reverse)
            else:
                self.paths.sort(reverse=sort_reverse)
        self.size = len(self.paths)

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        assert isinstance(idx, int)
        path = self.paths[idx]
        abspath = os.path.join(self.dirpath, path)
        doc = Document.load(abspath, fmt=self.fmt)
        doc.features[self.idxfeatname()] = idx
        # doc.features["__idx"] = idx
        # doc.features["__relpath"] = path
        # doc.features["__abspath"] = abspath
        return doc

    def __setitem__(self, idx, doc):
        """
        Set the document for a specific index.

        Args:
            idx: the index of the document
            doc: the Document, if None, no action is performed and the existing document is left unchanged
        """
        if doc is None:
            return
        assert isinstance(idx, int)
        assert isinstance(doc, Document)
        path = self.paths[idx]
        doc.save(os.path.join(self.dirpath, path), fmt=self.fmt)


class NumberedDirFilesCorpus(Corpus, MultiProcessingAble):
    """
    A corpus that represents files from a (nested) directory, where the filename is derived from
    the index number of the document. This corpus can represent missing elements as None, both
    on reading (when the corresponding expected document does not exist) and on writing (the
    corresponding document gets deleted).
    """

    def __init__(
        self,
        dirpath,
        digits=1,
        levels=1,
        ext="bdocjs",
        fmt=None,
        size=None,
        store_none=True,
    ):
        """
        Creates the NumberedDirFilesCorpus. This corpus, is able to return None for non-existing documents
        and remove document files by setting to None depending on the parameters.

        Args:
            dirpath: the directory path
            digits: the number of digits to use for the file path
            levels: the number of levels to split the digits up which are then used as subdire names.
            ext: the file extension used for all files in the corpus
            fmt: the format to use, if None, determined from the extension
            size: the size of the corpus. This can be used to create a corpus from an empty directory
                to contain only None elements initially.  It can also be used to limit access to only the
                first size elements if the directory contains more documents.
            store_none: if True, will store None in the corpus, i.e. remove the corresponding file from
                the directory. If False, will ignore the action and leave whatever is at the index unchanged.
        """
        if not ext.startswith("."):
            ext = "." + ext
        self.dirpath = dirpath
        self.ext = ext
        self.fmt = fmt
        self.size = size
        self.store_none = store_none
        self.file_path_maker = maker_file_path_fromidx(digits, levels)

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        assert isinstance(idx, int)
        path = self.file_path_maker(idx)
        path = path + self.ext
        abspath = os.path.join(self.dirpath, path)
        if os.path.exists(path):
            doc = Document.load(abspath, fmt=self.fmt)
            doc.features[self.idxfeatname()] = idx
            # doc.features["__idx"] = idx
            # doc.features["__relpath"] = path
            # doc.features["__abspath"] = abspath
        else:
            doc = None
        return doc

    def __setitem__(self, idx, doc):
        assert isinstance(idx, int)
        assert doc is None or isinstance(doc, Document)
        path = self.file_path_maker(idx)
        path = path + self.ext
        if doc is None:
            if self.store_none:
                if os.path.exists(path):
                    os.remove(path)
        else:
            Document.save(os.path.join(self.dirpath, path), fmt=self.fmt)