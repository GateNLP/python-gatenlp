"""
Module for testing the ChangeLog class.
"""


class TestChangeLog01:

    def test_changelog01m01(self):
        """
        Unit test method (make linter happy)
        """
        from gatenlp.document import Document, OFFSET_TYPE_JAVA
        from gatenlp.changelog import ChangeLog
        from gatenlp.offsetmapper import OffsetMapper

        chlog = ChangeLog()
        doc1 = Document("Just a simple \U0001F4A9 document.", changelog=chlog)
        annset1 = doc1.annset("")
        ann1 = annset1.add(0, 4, "Token", {"n": 1, "upper": True})
        ann2 = annset1.add(5, 6, "Token", {"n": 2, "upper": False})
        ann3 = annset1.add(7, 13, "Token", {"n": 3, "upper": False})
        _ann4id = annset1.add(
            14, 15, "Token", {"n": 4, "upper": False, "isshit": True}
        ).id
        ann5 = annset1.add(16, 24, "Token", {"n": 5})
        assert annset1.first().id == ann1.id
        assert annset1.last().id == ann5.id
        annset2 = doc1.annset("Set2")
        annset2.add(0, 12, "Ann1", None)
        annset1.remove(ann2)
        ann3b = annset1.get(ann3.id)
        ann3b.features["str"] = "simple"
        doc1.features["docfeature1"] = "value1"
        doc1.features["docfeature1"] = "value1b"
        chlog1 = doc1.changelog
        # print("!!!!!!!!!!!!!!DEBUG: ",chlog1.pprint())
        assert chlog1.changes[4].get("end") == 24
        assert chlog.changes[4].get("end") == 24
        om = OffsetMapper(doc1.text)
        jsonstr = chlog.save_mem(offset_type=OFFSET_TYPE_JAVA, offset_mapper=om)
        chlog2 = ChangeLog.load_mem(jsonstr, offset_mapper=om)
        assert chlog.changes[4].get("end") == 24
        assert chlog1.changes[4].get("end") == 24
        assert chlog2.changes[4].get("end") == 24

        # check if adding the changelog later works
        chlog = ChangeLog()
        doc1 = Document("Just a simple \U0001F4A9 document.")
        doc1.changelog = chlog
        annset1 = doc1.annset("")
        _ann1 = annset1.add(0, 4, "Token", {"n": 1, "upper": True})
        ann2 = annset1.add(5, 6, "Token", {"n": 2, "upper": False})
        ann3 = annset1.add(7, 13, "Token", {"n": 3, "upper": False})
        _ann4 = annset1.add(14, 15, "Token", {"n": 4, "upper": False, "isshit": True})
        _ann5 = annset1.add(16, 24, "Token", {"n": 5})
        annset2 = doc1.annset("Set2")
        annset2.add(0, 12, "Ann1", None)
        annset1.remove(ann2.id)
        ann3b = annset1.get(ann3.id)
        ann3b.features["str"] = "simple"
        doc1.features["docfeature1"] = "value1"
        doc1.features["docfeature1"] = "value1b"
        assert len(doc1.changelog) == len(chlog1)

        # test removing all annotations
        assert len(annset1) == 4
        annset1.clear()
        assert len(annset1) == 0


class TestAnnotationSet01:

    def test_annotationset01m01(self):
        """
        Unit test method (make linter happy)
        """
        from gatenlp.document import Document

        txt = " ".join([f"word{i:02d}" for i in range(10)])
        doc = Document(txt)
        annset = doc.annset()
        # create a Token annotation for each word
        # create "At3_1" annotations for a single token whenever i is a multiple of 3
        # create "At3_2" annotations for two tokens whenever i is a multiple of 3
        for i in range(10):
            annset.add(i * 7, i * 7 + 6, "Token", features={"i": i})
            if i % 3 == 0:
                annset.add(i * 7, i * 7 + 6, "At3_1", features={"i": i})
                # cannot span two tokens at the very end
                if i < 9:
                    annset.add(i * 7, i * 7 + 6 + 7, "At3_2", features={"i": i})
        # check: get all Token annotations
        ret = annset.with_type("Token")
        assert len(ret) == 10
        # check get all At3_1 annotations
        ret = annset.with_type("At3_1")
        assert len(ret) == 4
        ret = annset.with_type("At3_2")
        assert len(ret) == 3
        ret = annset.with_type("Token", "At3_1")
        assert len(ret) == 14
        ret = annset.with_type("At3_1", "Token")
        assert len(ret) == 14
        ret = annset.with_type("Token", "At3_1", non_overlapping=True)
        # print(f"\n!!!!!!!!!!!!DEBUG: anns for Token/At3_1={ret}")
        assert len(ret) == 10
        ret = annset.with_type("Token", "At3_2", non_overlapping=True)
        # print(f"\n!!!!!!!!!!!!DEBUG: anns for Token/At3_2={ret}")
        assert len(ret) == 10
        ret = annset.with_type("At3_1", "Token", non_overlapping=True)
        # print(f"\n!!!!!!!!!!!!DEBUG: anns for At3_1/Token={ret}")
        assert len(ret) == 10
        ret = annset.with_type("At3_2", "Token", non_overlapping=True)
        # print(f"\n!!!!!!!!!!!!DEBUG: anns for At3_2/Token={ret}")
        assert len(ret) == 7
        # TODO: check other kinds of overlap in the original set!
