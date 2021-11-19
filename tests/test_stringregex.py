"""
Module for testing the StringGazetteer
"""
from gatenlp.document import Document
import re
from gatenlp.processing.gazetteer.stringregex import StringRegexAnnotator, subst, one_or, replace_group, GroupNumber
from gatenlp.processing.gazetteer.stringregex import Rule, Action

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

RULES1 = """
DD=[0-2][0-9]|30|31
MM=[0][0-9]|10|11|12
YYYY=19[0-9][0-9]|20[0-9][0-9]
date_iso=({{YYYY}})-({{MM}})-({{DD}})
date_euro=({{DD}})/({{MM}})/({{YYYY}})
date_us=({{MM}})/({{DD}})/({{YYYY}})

|{{date_iso}}
0 => Date type="iso", date=G0, year=G1, month=G2, day=G3
1 => Year year=G1
2 => Month month=G2
3 => Day day=G3

|{{date_euro}}
0 => Date type="euro", date=G0, year=G3, month=G2, day=G1

|{{date_us}}
0 => Date type="us", date=G0, year=G3, month=G1, day=G2
"""


class TestStringRegexAnnotator:

    def test_subst(self):
        assert subst("asdf{{x}}fff", dict()) == "asdf{{x}}fff"
        assert subst("asdf{{x}}fff", dict(x=12)) == "asdf(?:12)fff"
        assert subst("asdf{{x}}fff", dict(x="text{{y}}text")) == "asdf(?:text{{y}}text)fff"
        assert subst("asdf{{x}}fff", dict(x="text{{y}}text", y=99)) == "asdf(?:text(?:99)text)fff"

    def test_oneor(self):
        g1 = iter([0, 1])
        assert one_or(g1, 15) == 0
        assert one_or(g1, 15) == 1
        assert one_or(g1, 15) == 15

    def test_replace_group(self):
        f1 = dict(a="x", b=GroupNumber(0), c=GroupNumber(1))
        assert replace_group(f1, ((0,1,"ALL"), (1,2,"Group1"), (2,3,"Group2"))) == dict(a="x", b="ALL", c="Group1")

    def test_pat1(self):
        rules1 = """
        |[abc]
        |[012]
        0 => Match
        """
        annt = StringRegexAnnotator(source=rules1, source_fmt="string")
        assert annt.rules is not None
        assert len(annt.rules) == 1
        r0 = annt.rules[0]
        assert isinstance(r0, Rule)
        pat = r0.pattern
        assert pat.pattern == '(?:[abc])|(?:[012])'

    def test_pat2(self):
        rules1 = """
        |[abc]
        +[012]
        0 => Match
        """
        annt = StringRegexAnnotator(source=rules1, source_fmt="string")
        assert annt.rules is not None
        assert len(annt.rules) == 1
        r0 = annt.rules[0]
        assert isinstance(r0, Rule)
        pat = r0.pattern
        assert pat.pattern == '(?:[abc][012])'

    def test_pat3(self):
        rules1 = """
        |[abc]
        +[012]
        |[xyz]
        0 => Match
        """
        annt = StringRegexAnnotator(source=rules1, source_fmt="string")
        assert annt.rules is not None
        assert len(annt.rules) == 1
        r0 = annt.rules[0]
        assert isinstance(r0, Rule)
        pat = r0.pattern
        assert pat.pattern == '(?:[abc][012])|(?:[xyz])'


    def test_misc1(self):
        """
        Unit test method (make linter happy)
        """
        annt = StringRegexAnnotator(source=RULES1, source_fmt="string", select_rules="all")
        # for rule in annt.rules:
        #     print(f"DEBUG: rule=", rule)

        # first of all, check if we got the rules parsed correctly
        assert annt.rules is not None
        assert len(annt.rules) == 3
        for r in annt.rules:
            assert isinstance(r, Rule)
            pat = r.pattern
            assert hasattr(pat, "match")
            assert hasattr(pat, "search")
            acts = r.actions
            assert isinstance(acts, list)
            assert len(acts) > 0
        pat0 = annt.rules[0].pattern
        acts0 = annt.rules[0].actions
        pat1 = annt.rules[1].pattern
        acts1 = annt.rules[1].actions

        assert len(acts0) == 4
        assert len(acts1) == 1

        for idx, a in enumerate(acts0):
            # print(f"\nDEBUG action {idx} is {a}")
            assert isinstance(a, Action)
            assert isinstance(a.groupnumbers, list)
            assert len(a.groupnumbers) == 1
            assert a.groupnumbers[0] == idx
            assert a.typename is not None
            assert isinstance(a.typename, str)
            assert a.features is not None
            assert isinstance(a.features, dict)
            if idx == 0:
                assert a.typename == "Date"
                assert "date" in a.features
                assert "day" in a.features
            if idx == 3:
                assert a.typename == "Day"

        # test if match_next works
        ret = annt.match_next(pat0, "some text 2021-12-21 some more")
        assert ret is not None
        assert len(ret) == 4
        start, end, groups, flag = ret
        assert start == 10
        assert end == 20
        assert groups is not None
        assert not flag
        assert len(groups) == 4
        assert groups[0] == (10, 20, "2021-12-21")

        ret = list(annt.find_all("asdf"))
        assert len(ret) == 0
        ret = list(annt.find_all("asdf 2013-12-21 dfdf "))
        assert len(ret) == 4

        ret = list(annt.find_all("asdf 02/09/2013 dfdf ", select_rules="last"))
        assert ret is not None
        assert len(ret) == 1
        m = ret[0]
        assert m.start == 5
        assert m.end == 15
        assert m.features is not None
        assert isinstance(m.features, dict)
        assert m.features["type"] == "us"
        assert m.type == "Date"

        ret = list(annt.find_all("asdf 02/09/2013 dfdf ", select_rules="first"))
        assert ret is not None
        assert len(ret) == 1
        m = ret[0]
        assert m.start == 5
        assert m.end == 15
        assert m.features is not None
        assert isinstance(m.features, dict)
        assert m.features["type"] == "euro"
        assert m.type == "Date"

        ret = list(annt.find_all("asdf 02/09/2013 dfdf ", select_rules="all"))
        assert ret is not None
        assert len(ret) == 2
        m = ret[0]
        assert m.start == 5
        assert m.end == 15
        assert m.features is not None
        assert isinstance(m.features, dict)
        assert m.features["type"] == "euro"
        assert m.type == "Date"
        m = ret[1]
        assert m.start == 5
        assert m.end == 15
        assert m.features is not None
        assert isinstance(m.features, dict)
        assert m.features["type"] == "us"
        assert m.type == "Date"

        # now run the actual annotator on a document
        doc1 = Document("asdf 02/09/2013 dfdf ")
        doc1 = annt(doc1)
        anns = doc1.annset()
        for idx, ann in enumerate(anns):
            assert ann.type == "Date"
            assert ann.start == 5
            assert ann.end == 15
            assert ann.features.get("year") == "2013"
            assert ann.features.get("date") == "02/09/2013"
