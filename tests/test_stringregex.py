"""
Module for testing the StringGazetteer
"""
from gatenlp.document import Document
import re
from gatenlp.processing.gazetteer.stringregex import StringRegexAnnotator, subst

DOC1_TEXT = "A simple document which has a number of words in it which we will use to test matching, simple document"


def makedoc(text=DOC1_TEXT):
    """
    Create and return document for testing.
    """
    doc1 = Document(text)
    set1 = doc1.annset()
    whitespaces = [
        m for m in re.finditer(r"[\s,.!?]+|^[\s,.!?]*|[\s,.!?]*$", text)
    ]
    nrtokens = len(whitespaces) - 1
    for k in range(nrtokens):
        fromoff = whitespaces[k].end()
        tooff = whitespaces[k + 1].start()
        set1.add(fromoff, tooff, "Token")
    return doc1


class TestStringRegexAnnotator:

    def test_subst(self):
        assert subst("asdf{{x}}fff", dict()) == "asdf{{x}}fff"
        assert subst("asdf{{x}}fff", dict(x=12)) == "asdf12fff"
        assert subst("asdf{{x}}fff", dict(x="text{{y}}text")) == "asdftext{{y}}textfff"
        assert subst("asdf{{x}}fff", dict(x="text{{y}}text", y=99)) == "asdftext99textfff"

    def test_create1(self):
        """
        Unit test method (make linter happy)
        """
        annt = StringRegexAnnotator()

