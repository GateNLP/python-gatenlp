"""
Module that defines Corpus and DocumentSource/DocumentDestination classes which access documents
as lines or parts in a file.
"""

from typing import Optional, Union, List, Dict, IO
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


def _update_dict_from_dict_4spec(todict, fromdict, spec, exclude_key=None, exclude4underscore=False):
    """
    Helper function for updating the todoct dict-like object from the fromdict dict-like object, according to
    spec, where spec is either None/False (do not update anything), True (include all but the exclude_key and
    keys starting with an underscore if exclude4underscore is True), a list of keys to update (if they are
    present in the from dict), or a dictionary, mapping which name in the fromdict to update as which key in
    the todict.

    Returns:
         nothing, the todict dictionary is updated in place
    """
    if not spec:
        return
    if spec is True:
        spec = {}
        for k in fromdict.keys():
            if k != exclude_key:
                if exclude4underscore and k.startswith("_"):
                    continue
                spec[k] = k
    elif isinstance(spec, list):
        specnew = {}
        for k in spec:
            if k != exclude_key:
                if exclude4underscore and k.startswith("_"):
                    continue
                specnew[k] = k
        spec = specnew
    elif not isinstance(spec, dict):
        raise Exception(f"Must specify None, boolean, a list of names or a map of names to names, not {spec}")
    for kfrom, kto in spec.items():
        if kfrom in fromdict:
            todict[kto] = fromdict[kfrom]


class JsonLinesFileSource(DocumentSource, MultiProcessingAble):
    """
    A document source which reads one json serialization per line, creates a document from one field
    in the json and optionally stores all or a selection of remaining fields as document features or
    into a single document feature "__data".
    """

    def __init__(
            self,
            file: str,
            text_field: str = "text",
            feature_fields: Optional[Union[bool, List[str], Dict[str, str]]] = None,
            data_fields: Optional[Union[bool, List[str], Dict[str, str]]] = None,
            data_feature: Optional[str] = "__data" ):
        """
        Create a JsonLinesFileSource.

        Args:
            file: the file path (a string) or an open file handle.
            text_field: the field name where to get the document text from. If a json object does not contain
                this field, the empty string is used instead.
            feature_fields: if not None and not False: either a list of field names which will get stored as
                features with the same name, or a dictionary mapping json fields to feature names, or True to
                indiciate that all fields (except the one containing the document text and fields where the field
                name starts with an underscore) get stored as features.
            data_fields: if not None and not False: either a list of field names which will get stored in the data
                feature as fields with the same name, or a dictionary mapping json fields to new names, or True to
                indiciate that all fields (except the one containing the document text) get stored in the data feature.
                The data feature should be a transient feature (the name starts with two underscores), the
                name for that feature is specified through the data_feature parameter
            data_feature:  the name of the data feature if used (if None, "__data" is used)
        """
        super().__init__()
        self.file = file
        self.text_field = text_field
        self.feature_fields = feature_fields
        self.data_fields = data_fields
        if data_feature is None:
            data_feature = "__data"
        self.data_feature = data_feature
        self.fh: IO = open(self.file, "rt", encoding="utf-8")

    def __iter__(self):
        for line in self.fh:
            data = json.loads(line)
            text = data.get(self.text_field, "")
            doc = Document(text)
            _update_dict_from_dict_4spec(
                doc.features, data, self.feature_fields,
                exclude_key=self.text_field, exclude4underscore=self.feature_fields is True)
            if self.data_fields:
                doc.features[self.data_feature] = {}
                _update_dict_from_dict_4spec(
                    doc.features[self.data_feature], data, self.data_fields,
                    exclude_key=self.text_field, exclude4underscore=False)
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
            file: Union[str, IO],
            text_field: str = "text",
            document_bdocjs: bool = False,
            feature_fields: Optional[Union[bool, List[str], Dict[str, str]]] = None,
            data_fields: Optional[Union[bool, List[str], Dict[str, str]]] = None,
            data_feature="__data"):
        """

        Args:
            file: the file to write to. If it exists, it gets overwritten without warning.
               Expected to be a string or an open file handle.
            text_field: the name of the json field that will contain the document either just the text or
               the bdocjs representation if document_bdocjs is True.
            document_bdocjs: if True store the bdocjs serialization into the document_field instead of just the text
            feature_fields: if not None and not False: either a list of features names which will get stored as
                fields with the same name, or a dictionary mapping feature names to field names, or True to
                indiciate that all features (except the one containing the document text and features where the field
                name starts with an underscore) get stored as fields.
            data_fields: if not None and not False: either a list of feature names from the data feature which will get
                stored as fields with the same name, or a dictionary mapping feature to field names, or True to
                indiciate that all features (except the one containing the document text) get stored as fields.
            data_feature:  the name of the data feature if used (if None, "__data" is used)
        """
        super().__init__()
        if isinstance(file, str):
            self.fh = open(file, "wt", encoding="utf-8")
        else:
            self.fh = file
        self.text_field = text_field
        self.document_bdocjs = document_bdocjs
        self.feature_fields = feature_fields
        self.data_fields = data_fields
        if data_feature is None:
            data_feature = "__data"
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
        _update_dict_from_dict_4spec(
            data,
            doc.features,
            self.feature_fields,
            exclude_key=self.text_field, exclude4underscore=self.feature_fields is True)
        _update_dict_from_dict_4spec(
            data,
            doc.features.get(self.data_feature, {}), self.data_fields,
            exclude_key=self.text_field, exclude4underscore=False)
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

