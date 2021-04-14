"""
Module for testing the Document class.
"""
import json
from gatenlp.document import Document, OFFSET_TYPE_JAVA
from gatenlp.span import Span


class TestDocument01:

    def test_document01m01(self):
        """
        Unit test method (make linter happy)
        """
        doc1 = Document(
            "This is a \U0001F4A9 document.\n이것은 문서입니다 \U0001F4A9\nЭто \U0001F4A9 документ\nاین یک سند \U0001F4A9 است"
        )
        annset1 = doc1.annset("")
        ann1 = annset1.add(8, 9, "Type1", {"f1": 1, "f2": 2})
        ann1id = ann1.id
        assert ann1id == 0
        assert len(annset1) == 1
        assert ann1.features["f1"] == 1
        ann2id = annset1.add(0, 4, "Type1", {"f1": 13, "f2": 12}).id
        assert ann2id == 1
        inorder = list(annset1.iter())
        assert len(inorder) == 2
        assert inorder[0].features["f1"] == 13
        assert inorder[1].features["f1"] == 1
        ann3 = annset1.add(0, 22, "Type2", {"feat1": True})
        ann3id = ann3.id
        assert ann3id in annset1
        assert annset1.span == Span(0, 22)
        retset1 = annset1.within(0, 10)
        # print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!DEBUG: ", retset1)
        assert retset1.isdetached()
        assert retset1.immutable
        assert retset1.size == 2
        assert len(retset1) == 2
        assert len(annset1.within(0, 10)) == 2
        assert len(annset1.within(1, 3)) == 0
        assert len(annset1.within(0, 22)) == 3
        doc1.features["docfeat1"] = 33
        assert doc1.features["docfeat1"] == 33
        # print("DOC: {}".format(doc1), file=sys.stderr)
        jsonstr = doc1.save_mem(offset_type=OFFSET_TYPE_JAVA)
        # print("JSON JAVA: {}".format(jsonstr), file=sys.stderr)
        doc2 = Document.load_mem(jsonstr)
        # print("DOC BACK: {}".format(doc2), file=sys.stderr)
        assert doc2.features["docfeat1"] == 33
        d2annset1 = doc2.annset("")
        assert len(d2annset1) == 3
        at8 = d2annset1.startingat(8)
        # print("AT8: {}".format(at8), file=sys.stderr)
        assert len(at8) == 1
        doc1.to_offset_type(OFFSET_TYPE_JAVA)
        jsonstr2 = doc1.save_mem()
        data = json.loads(jsonstr2)
        anndicts = data["annotation_sets"][""]["annotations"]
        assert anndicts[2]["end"] == 23

    def test_document01m02(self):
        """
        Unit test method (make linter happy)
        """
        from gatenlp.document import Document
        from gatenlp.changelog import ChangeLog
        chl = ChangeLog()
        doc1 = Document("some document", changelog=chl)
        doc1.name = "name"
        assert chl.changes is not None
        assert len(chl.changes) == 1
        assert chl.changes[0]["name"] == "name"

    def test_document01m03(self):
        """
        Unit test method (make linter happy)
        """
        doc = Document()
        assert doc.text is None
        doc.text = "some text"
        assert doc.text == "some text"
