"""
Module that defines DocumentDestination classes for exporting specific formats.
"""
import os
from typing import Union, Optional, List, Dict, IO
from gatenlp.corpora import DocumentDestination
from gatenlp import Document
from gatenlp.chunking import doc_to_ibo


class Conll2003FileDestination(DocumentDestination):
    """
    Extracts tokens and BIO-like codes from the documents and writes those in CONLL (2003) format.
    """

    def __init__(
            self,
            file: Union[str, IO],
            annset_name: str = "",
            sentence_type: Optional[str] = None,
            token_type: str = "Token",
            token_feature: Optional[str] = None,
            chunk_annset_name: Optional[str] = None,
            chunk_types: Optional[List[str]] = None,
            type2code: Optional[Dict] = None,
            scheme: str = "BIO",
):
        """
        Create a Conll2003FileDestination to write CONLL 2003 format data to a file.

        Args:
            file: either the file path (str) or an open file handle for writing
            annset_name: the annotation set which contains the annotation types needed
            sentence_type: if None, use whole document, otherwise generate one result per sentence type annotation,
                if the sentence contains at least one token.
            token_type: type of token annotations to use
            token_feature: if not None, use the feature instead of the covered document text
            chunk_annset_name: is specified, the annotation set name to use for retrieving the chunk annotations,
                otherwise annset_name is used for the chunk annotations too.
            chunk_types: a list of annotation types which identify chunks, each chunk type is used as entity type
                Note the chunk type annotations must not overlap, but this is currently not checked, for performance
                reasons.
            type2code: an optionam dict mapping the chunk_type to the type name used in the BIO codes
            scheme: the encoding scheme to use, default is BIO, possible: IOB, BIO, IOBES, BILOU, BMEOW, BMEWO
        """
        super().__init__()
        if isinstance(file, str):
            self.fh = open(file, "wt", encoding="utf-8")
        else:
            self.fh = file
        self.annset_name = annset_name
        self.sentence_type = sentence_type
        self.token_type = token_type
        self.token_feature = token_feature
        self.chunk_annset_name = chunk_annset_name
        self.chunk_types = chunk_types
        self.type2code = type2code
        self.scheme = scheme

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
        for sentence_rows in doc_to_ibo(
                doc,
                annset_name=self.annset_name,
                sentence_type=self.sentence_type,
                token_type=self.token_type,
                token_feature=self.token_feature,
                chunk_annset_name=self.chunk_annset_name,
                chunk_types=self.chunk_types,
                type2code=self.type2code,
                scheme=self.scheme
        ):
            for token, code in sentence_rows:
                print(token, code, sep="\t", file=self.fh)
            print(file=self.fh)  # empty line for sentence boundary
        self._n += 1

    def close(self):
        self.fh.close()


