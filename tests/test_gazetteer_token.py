import sys
import os
import pytest
from gatenlp.document import Document
import re
from gatenlp.processing.gazetteer import TokenGazetteer

DOC1_TEXT = "A simple document which has a number of words in it which we will use to test matching"


def makedoc1():
    doc1 = Document(DOC1_TEXT)
    set1 = doc1.annset()
    whitespaces = [
        m for m in re.finditer(r"[\s,.!?]+|^[\s,.!?]*|[\s,.!?]*$", DOC1_TEXT)
    ]
    nrtokens = len(whitespaces) - 1
    for k in range(nrtokens):
        fromoff = whitespaces[k].end()
        tooff = whitespaces[k + 1].start()
        set1.add(fromoff, tooff, "Token")
    return doc1


# no reference to list features
GAZLIST1 = [
    (["simple", "document"], {"match": 1}),
    (["has"], {"match": 2}),
    (["has", "a"], {"match": 3}),
    (["has", "a", "number"], {"match": 4}),
    (["has", "a", "number"], {"match": 5}),
]

# reference to list features of list 2
GAZLIST2 = [
    (["simple", "document"], {"match": 11}),
    (["has"], {"match": 22}),
    (["has", "a"], {"match": 33}),
    (["has", "a", "number"], {"match": 44}),
    (["has", "a", "number"], {"match": 55}),
]

# three lists, so we have three elements in the list with features for each list
LISTFEATURES1 = {"list": 0, "feat1": "somevalue1"}


class TestTokenGazetteer1:
    def test_create(self):
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        # print("\n!!!!!!!!!!! nodes=", gaz.nodes, "\n")
        assert gaz.nodes is not None
        assert "simple" in gaz.nodes
        assert "has" in gaz.nodes
        node1 = gaz.nodes["simple"]
        # print("\n!!!!!!!!!!! node1=", node1, "\n")
        assert not node1.is_match
        assert node1.data is None
        assert node1.nodes is not None
        assert len(node1.nodes) == 1
        assert "document" in node1.nodes
        node2 = node1.nodes["document"]
        # print("\n!!!!!!!!!!! node2=", node2, "\n")
        assert node2.is_match
        assert node2.data is not None
        assert node2.nodes is None
        assert len(node2.data) == 1
        node2data = node2.data[0]
        assert node2data == {"match": 1}

    def test_match1(self):
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        doc = makedoc1()
        toks = list(doc.annset())
        # print("\n!!!!! DEBUG: tokens=", toks, "\n")
        ret = gaz.match(toks, doc=doc)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert ret == ([], 0)
        ret = gaz.match(toks, doc=doc, idx=1)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert len(ret) == 2
        matches, maxlen = ret
        assert len(matches) == 1
        assert maxlen == 2
        assert matches[0].start == 1
        assert matches[0].end == 3
        assert len(matches[0].data) == 1
        assert matches[0].data[0] == {"match": 1}

    def test_match2(self):
        # test lists
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        # add another list
        gaz.append(source=GAZLIST2, fmt="gazlist")
        doc = makedoc1()
        toks = list(doc.annset())
        # print("\n!!!!! DEBUG: tokens=", toks, "\n")
        ret = gaz.match(toks, doc=doc)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert ret == ([], 0)
        ret = gaz.match(toks, doc=doc, idx=1)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert len(ret) == 2
        matches, maxlen = ret
        assert len(matches) == 1
        assert maxlen == 2
        assert matches[0].start == 1
        assert matches[0].end == 3
        assert len(matches[0].data) == 2
        assert matches[0].data[0] == {"match": 1}
        assert matches[0].data[1] == {"match": 11}
        assert len(matches[0].listidx) == 2
        assert matches[0].listidx[0] == 0
        assert matches[0].listidx[1] == 1

    def test_match3(self):
        # match at position 4 where we should get several matches, match all=False
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        doc = makedoc1()
        toks = list(doc.annset())
        # print("\n!!!!! DEBUG: tokens=", toks, "\n")
        ret = gaz.match(toks, doc=doc)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert ret == ([], 0)
        ret = gaz.match(toks, doc=doc, idx=4, all=False)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert len(ret) == 2
        matches, maxlen = ret
        assert len(matches) == 1
        assert maxlen == 3
        assert matches[0].start == 4
        assert matches[0].end == 7
        assert len(matches[0].data) == 2
        assert matches[0].data[0] == {"match": 4}
        assert matches[0].data[1] == {"match": 5}

    def test_match4(self):
        # match at position 4 where we should get several matches, match all=True
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        doc = makedoc1()
        toks = list(doc.annset())
        # print("\n!!!!! DEBUG: tokens=", toks, "\n")
        ret = gaz.match(toks, doc=doc)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert ret == ([], 0)
        ret = gaz.match(toks, doc=doc, idx=4, all=True)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert len(ret) == 2
        matches, maxlen = ret
        assert len(matches) == 3
        assert maxlen == 3
        # not sure how reliable the sequence is here ...
        assert matches[0].start == 4
        assert matches[0].end == 5
        assert len(matches[0].data) == 1
        assert matches[0].data[0] == {"match": 2}
        assert matches[1].start == 4
        assert matches[1].end == 6
        assert len(matches[1].data) == 1
        assert matches[1].data[0] == {"match": 3}
        assert matches[2].start == 4
        assert matches[2].end == 7
        assert len(matches[2].data) == 2
        assert matches[2].data[0] == {"match": 4}
        assert matches[2].data[1] == {"match": 5}

    def test_find1(self):
        # search from position 0
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        doc = makedoc1()
        toks = list(doc.annset())
        ret = gaz.find(toks, doc=doc, fromidx=0)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert len(ret) == 3
        matches, maxlen, idx = ret
        assert len(matches) == 1
        assert idx == 1
        assert maxlen == 2
        assert matches[0].start == 1
        assert matches[0].end == 3
        assert len(matches[0].data) == 1
        assert matches[0].data[0] == {"match": 1}

    def test_find2(self):
        # search from position 2
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        doc = makedoc1()
        toks = list(doc.annset())
        ret = gaz.find(toks, doc=doc, fromidx=2, all=True)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert len(ret) == 3
        matches, maxlen, idx = ret
        assert idx == 4
        assert len(matches) == 3
        assert maxlen == 3
        assert matches[0].start == 4
        assert matches[0].end == 5
        assert len(matches[0].data) == 1
        assert matches[0].data[0] == {"match": 2}
        assert matches[1].start == 4
        assert matches[1].end == 6
        assert len(matches[1].data) == 1
        assert matches[1].data[0] == {"match": 3}
        assert matches[2].start == 4
        assert matches[2].end == 7
        assert len(matches[2].data) == 2
        assert matches[2].data[0] == {"match": 4}
        assert matches[2].data[1] == {"match": 5}

    def test_find3(self):
        # search from position 5, should not find anything
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        doc = makedoc1()
        toks = list(doc.annset())
        ret = gaz.find(toks, doc=doc, fromidx=5, all=True)
        # print("\n!!!!! DEBUG: ret=", ret, "\n")
        assert len(ret) == 3
        matches, maxlen, idx = ret
        assert maxlen == 0
        assert idx == None
        assert len(matches) == 0

    def test_findall(self):
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        doc = makedoc1()
        toks = list(doc.annset())
        ret = list(gaz.find_all(toks, doc=doc, fromidx=0, all=True))
        assert len(ret) == 2
        m1 = ret[0]
        assert len(m1) == 1
        m1_0 = m1[0]
        assert m1_0.start == 1
        assert m1_0.end == 3
        assert m1_0.data == [{"match": 1}]
        m2 = ret[1]
        assert len(m2) == 3

    def test_call1(self):
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist")
        doc = makedoc1()
        gaz(doc)
        anns = doc.annset().with_type("Lookup")
        assert len(anns) == 3
        # same but with all=True, skip=False
        gaz = TokenGazetteer(source=GAZLIST1, fmt="gazlist", all=True, skip=False)
        doc = makedoc1()
        gaz(doc)
        anns = doc.annset().with_type("Lookup")
        assert len(anns) == 5

    def test_call2(self):
        testdir = os.path.join(os.curdir, "tests")
        gazfile = os.path.join(testdir, "gaz1.def")
        gaz = TokenGazetteer(source=gazfile, fmt="gate-def")
        doc = makedoc1()
        gaz(doc)
        anns = doc.annset().with_type("Lookup")
        assert len(anns) == 2
        anns = doc.annset().with_type("GazType1")
        assert len(anns) == 1

    def test_call3(self):
        testdir = os.path.join(os.curdir, "tests")
        gazfile = os.path.join(testdir, "gaz1.def")
        gaz = TokenGazetteer(source=gazfile, fmt="gate-def", all=True, skip=False)
        doc = makedoc1()
        gaz(doc)
        anns = doc.annset().with_type("Lookup")
        assert len(anns) == 4
        anns = doc.annset().with_type("GazType1")
        assert len(anns) == 2
