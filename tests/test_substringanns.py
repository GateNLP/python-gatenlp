"""
Module for testing the StringGazetteer
"""
import pytest
from gatenlp.document import Document
from gatenlp.annotation_utils import annotate_substrings
DOC1_TEXT = "A simple document which has a number of words in it."
DOC1_SUBSTR_VALID1 = ["document", "has", "in"]
DOC1_SUBSTR_VALID2 = ["A", "simple", "document", "which", "has", "a", "number", "of", "words", "in", "it", "."]
DOC1_SUBSTR_INVALID1 = ["A", "simple", "short", "document", "which", "has"]


def test_annotate_substrings1():
    doc = Document(DOC1_TEXT)
    doc = annotate_substrings(doc, DOC1_SUBSTR_VALID1, outset_name="", annotate_gaps=False, raise_if_unmatched=True)
    tokens = list(doc.annset("").with_type("Token"))
    assert len(tokens) == 3
    assert doc[tokens[0]] == "document"
    assert doc[tokens[1]] == "has"
    assert doc[tokens[2]] == "in"


def test_annotate_substrings2():
    doc = Document(DOC1_TEXT)
    doc = annotate_substrings(doc, DOC1_SUBSTR_VALID2, outset_name="", annotate_gaps=False, raise_if_unmatched=True)
    tokens = list(doc.annset("").with_type("Token"))
    assert len(tokens) == len(DOC1_SUBSTR_VALID2)
    for substr, token in zip(DOC1_SUBSTR_VALID2, tokens):
        assert doc[token] == substr


def test_annotate_substrings3():
    doc = Document(DOC1_TEXT)
    with pytest.raises(Exception, match="Unmatched string 'short' in"):
        annotate_substrings(doc, DOC1_SUBSTR_INVALID1, outset_name="", annotate_gaps=False, raise_if_unmatched=True)


def test_annotate_substrings4():
    doc = Document(DOC1_TEXT)
    doc = annotate_substrings(doc, DOC1_SUBSTR_INVALID1, outset_name="", annotate_gaps=False, raise_if_unmatched=False)
    tokens = list(doc.annset("").with_type("Token"))
    assert len(tokens) == len(DOC1_SUBSTR_INVALID1) - 1
    shouldmatch = [s for s in DOC1_SUBSTR_VALID2 if s != "short"]
    for substr, token in zip(shouldmatch, tokens):
        assert doc[token] == substr


