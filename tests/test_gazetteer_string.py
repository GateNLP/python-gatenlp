"""
Module for testing the StringGazetteer
"""
from gatenlp.document import Document
import re
from gatenlp.processing.gazetteer import StringGazetteer

DOC1_TEXT = "A simple document which has a number of words in it which we will use to test matching"

DOC2_TEXT = "A simple document which has a number of words in it which we will use to test matching, simple document"


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


# no reference to list features
GAZLIST1 = [
    ("simple document", {"match": 1}),
    ("has", {"match": 2}),
    ("has a", {"match": 3}),
    ("has a number", {"match": 4}),
    ("has a number", {"match": 5}),
    ("completely different", {"match": 6})
]

# reference to list features of list 2
GAZLIST2 = [
    ("simple document", {"match": 11}),
    ("has", {"match": 22}),
    ("has a", {"match": 33}),
    ("has a number", {"match": 44}),
    ("has a number", {"match": 55}),
]

# three lists, so we have three elements in the list with features for each list
LISTFEATURES1 = {"list": 0, "feat1": "somevalue1"}


class TestStringGazetteer1:

    def test_create(self):
        """
        Unit test method (make linter happy)
        """
        gaz = StringGazetteer(source=GAZLIST1, source_fmt="gazlist")
        # print("\n!!!!!!!!!!! gaz=", gaz._root.format_node(recursive=False), "\n")
        assert gaz._root is not None
        assert "simple document" in gaz
        assert "has" in gaz
        node1 = gaz._get_node("simple")
        # print("\n!!!!!!!!!!! node1=", node1.format_node(), "\n")
        assert not node1.is_match()
        assert node1.value is None
        assert node1.listidxs is None

    def test_match1(self):
        """
        Unit test method (make linter happy)
        """
        gaz = StringGazetteer(source=GAZLIST1, source_fmt="gazlist")
        doc = makedoc()
        # toks = list(doc.annset())
        ret = gaz.match(doc.text, start=2)
        assert len(ret) == 2    # list of matches, length of longest match
        matches, longest = ret
        assert isinstance(matches, list)
        assert isinstance(longest, int)
        assert longest == 15
        assert len(matches) == 1
        match = matches[0]
        assert match.start == 2
        assert match.end == 17
        assert match.match == "simple document"
        assert isinstance(match.features, dict)
        assert isinstance(match.type, str)
        assert match.features == dict(match=1)
        assert match.type == "Lookup"

        ret = gaz.find(doc.text, start=17)
        matches, longest, where = ret
        assert len(matches) == 4
        assert longest == 12
        assert where == 24
        assert matches[0].match == "has"
        assert matches[1].match == "has a"
        assert matches[2].match == "has a number"
        assert matches[3].match == "has a number"

        # same but only find longest
        ret = gaz.find(doc.text, start=17, longest_only=True)
        matches, longest, where = ret
        assert len(matches) == 2
        assert longest == 12
        assert where == 24
        assert matches[0].match == "has a number"
        assert matches[1].match == "has a number"

        matches = list(gaz.find_all(doc.text))
        assert len(matches) == 5
        assert matches[0].match == "simple document"
        assert matches[1].match == "has"
        assert matches[2].match == "has a"
        assert matches[3].match == "has a number"
        assert matches[4].match == "has a number"

    def test_match2(self):
        """
        Unit test method (make linter happy)
        """
        gaz = StringGazetteer(source=GAZLIST1, source_fmt="gazlist")
        doc = makedoc()
        doc = gaz(doc)
        lookups = list(doc.annset().with_type("Lookup"))
        assert len(lookups) == 5
        assert lookups[0].start == 2
        assert lookups[0].end == 17
        assert doc[lookups[0]] == "simple document"

        assert lookups[1].start == 24
        assert lookups[1].end == 27
        assert doc[lookups[1]] == "has"
        assert lookups[1].features.get("match") == 2

        assert lookups[2].start == 24
        assert lookups[2].end == 29
        assert doc[lookups[2]] == "has a"
        assert lookups[2].features.get("match") == 3

        assert lookups[3].start == 24
        assert lookups[3].end == 36
        assert doc[lookups[3]] == "has a number"
        assert lookups[3].features.get("match") == 4

        assert lookups[4].start == 24
        assert lookups[4].end == 36
        assert doc[lookups[4]] == "has a number"
        assert lookups[4].features.get("match") == 5
