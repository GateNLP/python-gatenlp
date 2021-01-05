import sys
import os
import pytest
from gatenlp.document import Document
from gatenlp.corpora import ListCorpus, ShuffledCorpus, EveryNthCorpus

TEXTS = [
    "00 This is the first document.",
    "01 And this is the second document.",
    "02 Here is another one, document three.",
    "03 Yet another, this one is number four.",
    "04 Here is document five.",
    "05 This is the sixth document.",
    "06 Finally, document number seven.",
]


class TestCorpora1:
    def test_listcorpus(self):
        docs = [Document(t) for t in TEXTS]
        lc1 = ListCorpus(docs)
        assert len(lc1) == len(docs)
        for idx, doc in enumerate(lc1):
            assert idx == doc.features["__idx"]
            assert idx == doc.features[lc1.idxfeatname()]
            assert doc.text == TEXTS[idx]

        for doc in lc1:
            doc.features["test1"] = "updated"
            lc1.store(doc)
        assert lc1[0].features["test1"] == "updated"

        # wrap the list corpus into a shuffled corpus
        sc1 = ShuffledCorpus(lc1, seed=42)
        orig = [
            "00", "01", "02", "03", "04", "05", "06"
        ]
        shuffled = [
            "01", "03", "04", "02", "06", "00", "05"
        ]
        for idx, doc in enumerate(sc1):
            assert doc.text[:2] == shuffled[idx]
        for doc in sc1:
            sc1.store(doc)
        for idx, doc in enumerate(sc1):
            assert doc.text[:2] == shuffled[idx]
        for idx, doc in enumerate(lc1):
            assert doc.text[:2] == orig[idx]

        lc2 = ListCorpus.empty(10)
        assert len(lc2) == 10
        for doc in lc2:
            assert doc == None
