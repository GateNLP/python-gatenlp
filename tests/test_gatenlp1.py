import sys


class TestOffsetMapper01:

    def test_offsetmapper01m01(self):
        from gatenlp.document import OffsetMapper, Document
        import numpy as np
        c_poo = "\U0001F4A9"
        c_bridge = "\U0001f309"
        doc1 = Document("01"+c_poo+"3"+c_bridge+c_bridge+c_bridge+"7")
        assert doc1.size() == 8
        assert doc1[2] == c_poo
        om1 = OffsetMapper(doc1)
        assert len(om1.java2python) == 12
        p2j = np.array([0, 1, 2, 4, 5, 7, 9, 11])
        assert (om1.python2java == p2j).all()
        j2p = np.array([0, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6, 7])
        assert (om1.java2python == j2p).all()
        for i in om1.java2python:
            joff = om1.convert_to_java(i)
            poff = om1.convert_to_python(joff)
            assert poff == i


class TestDocument01:

    def test_document01m01(self):
        from gatenlp.document import Document, OFFSET_TYPE_JAVA
        from gatenlp.docformats import gatesimplejsondoc
        doc1 = Document("This is a \U0001F4A9 document.\n이것은 문서입니다 \U0001F4A9\nЭто \U0001F4A9 документ\nاین یک سند \U0001F4A9 است")
        annset1 = doc1.get_annotations("")
        ann1id = annset1.add(8, 9, "Type1", {"f1": 1, "f2": 2})
        assert len(annset1) == 1
        ann1 = annset1.get(ann1id)
        assert ann1.get_feature("f1") == 1
        ann2id = annset1.add(0, 4, "Type1", {"f1": 13, "f2": 12})
        inorder = list(annset1.in_document_order())
        assert len(inorder) == 2
        assert inorder[0].get_feature("f1") == 13
        assert inorder[1].get_feature("f1") == 1
        ann3id = annset1.add(0, 22, "Type2", {"feat1": True})
        assert ann3id in annset1
        assert annset1.span() == (0, 22)
        assert annset1.first() == annset1.get(ann2id)
        assert annset1.last() == annset1.get(ann1id)
        assert annset1.first(by_end=True) == annset1.get(ann2id)
        assert annset1.last(by_end=True) == annset1.get(ann3id)
        assert len(annset1.within(0, 10)) == 2
        assert len(annset1.within(1, 3)) == 0
        assert len(annset1.within(0, 22)) == 3
