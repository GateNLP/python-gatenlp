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
        self.file = file

    def __iter__(self):
        with open(self.file, "rt", encoding="utf-8") as infp:
            for line in infp:
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
        if isinstance(file, str):
            self.fh = open(file, "wt", encoding="utf-8")
        else:
            self.fh = file
        self.n = 0

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
        self.n += 1

    def close(self):
        self.fh.close()


class JsonLinesFileSource(DocumentSource, MultiProcessingAble):
    """
    A document source which reads one json serialization per line, creates a document from one field
    in the json and optionally stores all or a selection of remaining fields as document feature "__data".
    """

    def __init__(self, file, text_field="text", data_fields=None, data_feature="__data"):
        """
        Create a JsonLinesFileSource.

        Args:
            file: the file path (a string) or an open file handle.
            text_field: the field name where to get the document text from.
            data_fields: if a list of names, store these fields in the "__data" feature. if True, store all fields.
            data_feature: the name of the data feature, default is "__data"
        """
        #   feature_fields: NOT YET IMPLEMENTED -- a mapping from original json fields to document features

        self.file = file
        self.text_field = text_field
        self.data_fields = data_fields
        self.data_feature = data_feature

    def __iter__(self):
        with open(self.file, "rt", encoding="utf-8") as infp:
            for line in infp:
                data = json.loads(line)
                # TODO: what if the field does not exist? should we use get(text_field, "") instead?
                text = data[self.text_field]
                doc = Document(text)
                if self.data_fields:
                    if isinstance(self.data_fields, list):
                        tmp = {}
                        for fname in self.data_fields:
                            # TODO: what if the field does not exist?
                            tmp[fname] = data[fname]
                    else:
                        tmp = data
                    doc.features[self.data_feature] = tmp
                yield doc


class JsonLinesFileDestination(DocumentDestination):
    """
    Writes one line of JSON per document to the a single output file. This will either write the document json
    as nested data or the document text to the field designated for the document and will write other json
    fields from the "__data" document feature.
    """

    def __init__(self, file, document_field="text", document_bdocjs=False, data_fields=True, data_feature="__data"):
        """

        Args:
            file: the file to write to. If it exists, it gets overwritten without warning.
               Expected to be a string or an open file handle.
            document_field: the name of the json field that will contain the document either just the text or
               the bdocjs representation if document_bdocjs is True.
            document_bdocjs: if True store the bdocjs serialization into the document_field instead of just the text
            data_fields: if a list, only store these fields in the json, if False, do not store any additional fields.
               Default is True: store all fields as is.
            data_feature: the name of the data feature, default is "__data"
        """
        if isinstance(file, str):
            self.fh = open(file, "wt", encoding="utf-8")
        else:
            self.fh = file
        self.n = 0
        self.document_field = document_field
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
        if self.data_fields:
            if isinstance(self.data_fields, list):
                for fname in self.data_fields:
                    data[fname] = doc.features[self.data_feature][fname]
            else:
                data.update(doc.features[self.data_feature])
        # assign the document field last so it overwrites anything that comes from the data feature!
        if self.document_bdocjs:
            data[self.document_field] = doc.save_mem(fmt="json")
        else:
            data[self.document_field] = doc.text
        self.fh.write(json.dumps(data))
        self.fh.write("\n")
        self.n += 1

    def close(self):
        self.fh.close()


class TsvFileSource(DocumentSource, MultiProcessingAble):
    """
    A TsvFileSource is a DocumentSource which is a single TSV file with a fixed number of tab-separated
    values per row. Each document in sequence is created from the text in one of the columns and
    document features can be set from arbitrary columns as well.
    """

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
        assert text_col is not None
        self.hdr = hdr
        self.text_col = text_col
        self.feature_cols = feature_cols
        self.data_cols = data_cols
        self.source = source
        self.n = 0
        self.hdr2col = {}
        if data_cols and not hdr:
            raise Exception("Header must be present if data_cols should be used")
        self.data_feature = data_feature

    def __iter__(self):
        reader = yield_lines_from(self.source)
        if self.hdr and self.n == 0:
            self.n += 1
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
            self.n += 1
            yield doc
