import sys


class TestOffsetMapper01:

    def test_offsetmapper01m01(self):
        from gatenlp.document import OffsetMapper, Document
        c_poo = "\U0001F4A9"
        c_bridge = "\U0001f309"
        doc1 = Document("01"+c_poo+"3"+c_bridge+c_bridge+c_bridge+"7")
        assert doc1.size() == 8
        assert doc1[2] == c_poo
        om1 = OffsetMapper(doc1)
        assert len(om1.java2python) == 13
        p2j = [0, 1, 2, 4, 5, 7, 9, 11, 12]
        # print("p2j={}".format(p2j), file=sys.stderr)
        # print("om1.p2j={}".format(om1.python2java), file=sys.stderr)
        assert om1.python2java == p2j
        j2p = [0, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6, 7, 8]
        assert om1.java2python == j2p
        for i in om1.java2python:
            joff = om1.convert_to_java(i)
            poff = om1.convert_to_python(joff)
            assert poff == i


class TestDocument01:

    def test_document01m01(self):
        from gatenlp.document import Document, OFFSET_TYPE_JAVA
        from gatenlp.docformats import simplejson
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
        assert len(annset1.within(0, 10)) == 2
        assert len(annset1.within(1, 3)) == 0
        assert len(annset1.within(0, 22)) == 3
        doc1.set_feature("docfeat1", 33)
        assert doc1.get_feature("docfeat1") == 33
        # print("DOC: {}".format(doc1), file=sys.stderr)
        jsonstr = simplejson.dumps(doc1, offset_type=OFFSET_TYPE_JAVA)
        # print("JSON JAVA: {}".format(jsonstr), file=sys.stderr)
        doc2 = simplejson.loads(jsonstr)
        # print("DOC BACK: {}".format(doc2), file=sys.stderr)
        assert doc2.get_feature("docfeat1") == 33
        d2annset1 = doc2.get_annotations("")
        assert len(d2annset1) == 3
        at8 = d2annset1.start_eq(8)
        # print("AT8: {}".format(at8), file=sys.stderr)
        assert len(at8) == 1


class TestChangeLog01:

    def test_changelog01m01(self):
        from gatenlp.document import Document, OFFSET_TYPE_JAVA
        from gatenlp.changelog import ChangeLog
        from gatenlp.offsetmapper import OffsetMapper
        from gatenlp.docformats import simplejson
        chlog = ChangeLog()
        doc1 = Document("Just a simple \U0001F4A9 document.", changelog=chlog)
        annset1 = doc1.get_annotations("")
        ann1id = annset1.add(0, 4, "Token", {"n": 1, "upper": True})
        ann2id = annset1.add(5, 6, "Token", {"n": 2, "upper": False})
        ann3id = annset1.add(7, 13, "Token", {"n": 3, "upper": False})
        ann4id = annset1.add(14, 15, "Token", {"n": 4, "upper": False, "isshit": True})
        ann5id = annset1.add(16, 24, "Token", {"n": 5})
        annset2 = doc1.get_annotations("Set2")
        annset2.add(0, 12, "Ann1", None)
        annset1.remove(ann2id)
        annset1.get(ann3id).set_feature("str", "simple")
        doc1.set_feature("docfeature1", "value1")
        doc1.set_feature("docfeature1", "value1b")
        chlog1 = doc1.changelog
        # print("Changelog:", chlog, file=sys.stderr)
        # print("Changelog:", file=sys.stderr)
        # chlog.format_to(sys.stderr)
        om = OffsetMapper(doc1)
        jsonstr = simplejson.dumps(chlog, offset_type=OFFSET_TYPE_JAVA, offset_mapper=om)
        # print("JSON:", jsonstr, file=sys.stderr)
        chlog2 = simplejson.loads(jsonstr, offset_mapper=om)
        # print("Changelog from JSON:", chlog2, file=sys.stderr)
        assert chlog2.changes[4].get("end") == 24

        # check if adding the changelog later works
        chlog = ChangeLog()
        doc1 = Document("Just a simple \U0001F4A9 document.")
        doc1.set_changelog(chlog)
        annset1 = doc1.get_annotations("")
        ann1id = annset1.add(0, 4, "Token", {"n": 1, "upper": True})
        ann2id = annset1.add(5, 6, "Token", {"n": 2, "upper": False})
        ann3id = annset1.add(7, 13, "Token", {"n": 3, "upper": False})
        ann4id = annset1.add(14, 15, "Token", {"n": 4, "upper": False, "isshit": True})
        ann5id = annset1.add(16, 24, "Token", {"n": 5})
        annset2 = doc1.get_annotations("Set2")
        annset2.add(0, 12, "Ann1", None)
        annset1.remove(ann2id)
        annset1.get(ann3id).set_feature("str", "simple")
        doc1.set_feature("docfeature1", "value1")
        doc1.set_feature("docfeature1", "value1b")
        assert len(doc1.changelog) == len(chlog1)

        # test removing all annotations
        assert len(annset1) == 4
        annset1.clear()
        assert len(annset1) == 0