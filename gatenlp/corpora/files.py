"""
Module that defines Corpus and DocumentSource/DocumentDestination classes which access documents
as lines or parts in a file.
"""

import json
from gatenlp.urlfileutils import yield_lines_from
from gatenlp.document import Document
from gatenlp.corpora.base import DocumentSource, DocumentDestination
from gatenlp.corpora.base import MultiProcessingAble


class BdocjsLinesFileSource(DocumentSource, MultiProcessingAble):
    """
    A document source which reads one bdoc json serialization of a document from each line of the given file.
    """

    def __init__(self, file):
        """
        Create a JsonLinesFileSource.

        Args:
            file: the file path (a string) or an open file handle.
        """
        super().__init__()
        self.file = file
        self.fh = open(self.file, "rt", encoding="utf-8")

    def __enter__(self):
        return self

    def __exit__(self, extype, value, traceback):
        self.fh.close()

    def close(self):
        self.fh.close()

    def __iter__(self):
        for line in self.fh:
            self._n += 1
            yield Document.load_mem(line, fmt="json")


class BdocjsLinesFileDestination(DocumentDestination):
    """
    Writes one line of JSON per document to the a single output file.
    """

    def __init__(self, file):
        """

        Args:
            file: the file to write to. If it exists, it gets overwritten without warning.
               Expected to be a string or an open file handle.
        """
        super().__init__()
        if isinstance(file, str):
            self.fh = open(file, "wt", encoding="utf-8")
        else:
            self.fh = file

    def __enter__(self):
        return self

    def __exit__(self, extype, value, traceback):
        self.fh.close()

    def append(self, doc):
        """
        Append a document to the destination.

        Args:
            doc: the document, if None, no action is performed.
        """
        if doc is None:
            return
        assert isinstance(doc, Document)
        self.fh.write(doc.save_mem(fmt="json"))
        self.fh.write("\n")
        self._n += 1

    def close(self):
        self.fh.close()


class JsonLinesFileSource(DocumentSource, MultiProcessingAble):
    """
    A document source which reads one json serialization per line, creates a document from one field
    in the json and optionally stores all or a selection of remaining fields as document features or
     into a single document feature "__data".
    """

    def __init__(
            self,
            file,
            text_field="text",
            data_fields=None,
            data_feature="__data"):
        """
        Create a JsonLinesFileSource.

        Args:
            file: the file path (a string) or an open file handle.
            text_field: the field name where to get the document text from. If a json object does not contain
                this field, the empty string is used instead.
            data_fields: if a list of names, store these fields in the "__data" feature. if True, store all fields.
                If a list is specified and a JSON object does not contain such a field, None is used instead.
            data_feature:  if this is None, the data fields are stored as features, otherwise, the data fields are
                all stored in a feature with this name as entries in a dict. Default is to use a feature with
                the name "__data".
        """
        #   feature_fields: NOT YET IMPLEMENTED -- a mapping from original json fields to document features
        super().__init__()
        self.file = file
        self.text_field = text_field
        self.data_fields = data_fields
        self.data_feature = data_feature
        self.fh = open(self.file, "rt", encoding="utf-8")

    def __iter__(self):
        for line in self.fh:
            data = json.loads(line)
            text = data.get(self.text_field, "")
            doc = Document(text)
            if self.data_fields:
                if isinstance(self.data_fields, list):
                    tmp = {}
                    for fname in self.data_fields:
                        tmp[fname] = data.get(fname)
                else:
                    tmp = data
                if self.data_feature is not None:
                    doc.features[self.data_feature] = {}
                    for k, v in tmp.items():
                        if k != self.text_field:
                            doc.features[self.data_feature][k] = tmp[k]
                else:
                    for k, v in tmp.items():
                        if k != self.text_field:
                            doc.features[k] = tmp[k]
            self._n += 1
            yield doc

    def __enter__(self):
        return self

    def __exit__(self, extype, value, traceback):
        self.fh.close()

    def close(self):
        self.fh.close()



class JsonLinesFileDestination(DocumentDestination):
    """
    Writes one line of JSON per document to the a single output file. This will either write the document json
    as nested data or the document text to the field designated for the document and will write other json
    fields from the "__data" document feature.
    """

    def __init__(
            self,
            file,
            text_field="text",
            document_bdocjs=False,
            data_fields=True,
            data_feature="__data"):
        """

        Args:
            file: the file to write to. If it exists, it gets overwritten without warning.
               Expected to be a string or an open file handle.
            text_field: the name of the json field that will contain the document either just the text or
               the bdocjs representation if document_bdocjs is True.
            document_bdocjs: if True store the bdocjs serialization into the document_field instead of just the text
            data_fields: if a list, store these fields in the json, if False,
                do not store any field, if True (default) store all fields. The fields are taken from the document
                feature specified as data_feature, or if that is None, directly from the document features.
                If the fields are taken from document features and data_fields is True, only features with names that
                do nut start with an underscore are added.
            data_feature: the name of the data feature, default is "__data". If this is None, fields are saved
                directly from the document features instead.
        """
        super().__init__()
        if isinstance(file, str):
            self.fh = open(file, "wt", encoding="utf-8")
        else:
            self.fh = file
        self.text_field = text_field
        self.document_bdocjs = document_bdocjs
        self.data_fields = data_fields
        self.data_feature = data_feature

    def __enter__(self):
        return self

    def __exit__(self, _extype, _value, _traceback):
        self.fh.close()

    def append(self, doc):
        """
        Append a document to the destination.

        Args:
            doc: the document, if None, no action is performed.
        """
        if doc is None:
            return
        assert isinstance(doc, Document)
        data = {}
        if self.data_feature is None:
            src = doc.features
        else:
            src = doc.features[self.data_feature]
        if self.data_fields:
            if isinstance(self.data_fields, list):
                for fname in self.data_fields:
                    if fname != self.text_field:
                        data[fname] = src[fname]
            else:
                for fname in src.keys():
                    if fname != self.text_field:
                        if self.data_feature or (self.data_feature is None and not fname.startswith("_")):
                            data[fname] = src[fname]
        # assign the document field last so it overwrites anything that comes from the data feature!
        if self.document_bdocjs:
            data[self.text_field] = doc.save_mem(fmt="json")
        else:
            data[self.text_field] = doc.text
        self.fh.write(json.dumps(data))
        self.fh.write("\n")
        self._n += 1

    def close(self):
        self.fh.close()


class TsvFileSource(DocumentSource, MultiProcessingAble):
    """
    A TsvFileSource is a DocumentSource which is a single TSV file with a fixed number of tab-separated
    values per row. Each document in sequence is created from the text in one of the columns and
    document features can be set from arbitrary columns as well.
    """
    # TODO: better implementation where we make explicit use of the context manager and iterator
    def __init__(self, source, hdr=True, text_col=None, feature_cols=None, data_cols=None, data_feature="__data"):
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
            feature_cols: if not None, must be either a dictionary mapping document feature names to the
                column numbers or column names of where to get the feature value from;
                or a function that should take the list of fields and arbitrary kwargs and return a dictionary
                with the features. Also passes "cols" (dict mapping column names to column indices, or None) and
                "n" (current line number) as keyword arguments.
            data_cols: if not None, either an iterable of the names of columns to store in the special document
                feature "__data" or if "True", stores all columns. At the moment this only works if the tsv file
                has a header line. The values are stored as a list in the order of the names given or the original
                order of the values in the TSV file.
            data_feature: the name of the document feature where to store the data, default is "__data"
        """
        super().__init__()
        assert text_col is not None
        self.hdr = hdr
        self.text_col = text_col
        self.feature_cols = feature_cols
        self.data_cols = data_cols
        self.source = source
        self.hdr2col = {}
        self.nlines = 0
        if data_cols and not hdr:
            raise Exception("Header must be present if data_cols should be used")
        self.data_feature = data_feature

    def __iter__(self):
        reader = yield_lines_from(self.source)
        if self.hdr and self.nlines == 0:
            self.nlines += 1
            self.hdr = next(reader).rstrip("\n\r").split("\t")
        if self.hdr:
            self.hdr2col = {name: idx for idx, name in enumerate(self.hdr)}
        for line in reader:
            line = line.rstrip("\n\r")
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
            if self.data_cols:
                if isinstance(self.data_cols, list):
                    data = {}
                    for cname in self.data_cols:
                        if isinstance(cname, str):
                            data[cname] = fields[self.hdr2col[cname]]
                        else:
                            # assume it is the column index!
                            data[cname] = fields[cname]
                else:
                    data = fields
                doc.features[self.data_feature] = data
            self.nlines += 1
            self._n += 1
            yield doc

    def __enter__(self):
        return self

    def __exit__(self, extype, value, traceback):
        pass

    def close(self):
        pass

