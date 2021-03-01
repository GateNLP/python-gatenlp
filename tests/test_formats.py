import sys
import os
import pytest


DOC1_TEXT = "A simple document"


def makedoc1():
    from gatenlp.document import Document

    doc1 = Document(DOC1_TEXT)
    doc1.features["feat1"] = "value1"
    anns = doc1.annset()
    anns.add(0, 2, "Type1", dict(a=1, b=True, c="some string"))
    doc1.annset("Set2").add(2, 8, "Type2")
    return doc1


class TestFormatGateXml:
    def test_formatgatexml01(self):
        from gatenlp.document import Document

        curpath = os.path.abspath(os.path.curdir)
        tstpath = os.path.join(curpath, "tests")
        with pytest.raises(Exception) as ex:
            Document.load(source=os.path.join(tstpath, "testdoc1.xml"), fmt="gatexml")
        assert "Unsupported serialization type" in str(ex.value)
        doc = Document.load(
            source=os.path.join(tstpath, "testdoc1.xml"),
            fmt="gatexml",
            ignore_unknown_types=True,
        )
        fs = doc.features
        # print("\n!!!!!!!!!!!!!!!!!!!!!!!! FEATURES=", fs)
        assert "fInt1" in fs and fs["fInt1"] == 222
        assert "fBoolean" in fs and fs["fBoolean"] == True
        assert "fString1" in fs and fs["fString1"] == "Some string"
        assert "fLong1" in fs and fs["fLong1"] == 123
        assert "fFloat1" in fs and fs["fFloat1"] == 3.4
        anns = doc.annset()
        # print("\n!!!!!!!!!!!!!!!!!!!!!!!! ANNS=", anns)
        assert len(anns) == 2
        ann1, ann2 = list(anns)[0:2]
        assert ann1.type == "Type1"
        assert ann1.start == 0
        assert ann1.end == 4
        assert ann1.id == 0
        assert ann2.type == "Type1"
        assert ann2.start == 5
        assert ann2.end == 8
        assert ann2.id == 1


class TestFormatYaml:
    def test_formatyaml01(self):
        from gatenlp.document import Document

        curpath = os.path.abspath(os.path.curdir)
        tstpath = os.path.join(curpath, "tests")
        doc = Document.load(
            source=os.path.join(tstpath, "testdoc1.bdocym"), fmt="text/bdocym"
        )
        fs = doc.features
        # print("\n!!!!!!!!!!!!!!!!!!!!!!!! FEATURES=", fs)
        assert "fInt1" in fs and fs["fInt1"] == 222
        assert "fBoolean" in fs and fs["fBoolean"] == True
        assert "fString1" in fs and fs["fString1"] == "Some string"
        assert "fLong1" in fs and fs["fLong1"] == 123
        assert "fFloat1" in fs and fs["fFloat1"] == 3.4
        assert "fComplex1" in fs
        fc1 = fs["fComplex1"]
        assert "key1" in fc1
        assert "fComplex2a" in fs
        assert "fComplex2b" in fs
        assert "feat1" in fs["fComplex2a"]
        assert "feat1" in fs["fComplex2b"]
        fc2a = fs["fComplex2b"]["feat1"]
        fc2b = fs["fComplex2b"]["feat1"]
        assert "k2" in fc2a
        assert "k2" in fc2b
        assert fc2a["k2"] == fc2b["k2"]
        assert fc2a["k2"] is fc2b["k2"]
        anns = doc.annset()
        # print("\n!!!!!!!!!!!!!!!!!!!!!!!! ANNS=", anns)
        assert len(anns) == 2
        ann1, ann2 = list(anns)[0:2]
        assert ann1.type == "Type1"
        assert ann1.start == 0
        assert ann1.end == 4
        assert ann1.id == 0
        assert "fComplex2a" in ann1.features
        assert "k2" in ann1.features["fComplex2a"]
        assert fc2a["k2"] == ann1.features["fComplex2a"]["k2"]
        assert fc2a["k2"] is ann1.features["fComplex2a"]["k2"]

        assert ann2.type == "Type1"
        assert ann2.start == 5
        assert ann2.end == 8
        assert ann2.id == 1

    def test_formatyaml02(self):
        from gatenlp.document import Document

        doc1 = makedoc1()
        asjson = doc1.save_mem(fmt="text/bdocym")
        doc2 = Document.load_mem(asjson, fmt="text/bdocym")
        assert doc2.text == DOC1_TEXT
        assert len(doc1.features) == 1
        assert doc1.features.get("feat1") == "value1"
        assert len(doc1.annset()) == 1
        assert len(doc1.annset("Set2")) == 1
        ann1 = doc1.annset().first()
        assert ann1.type == "Type1"
        assert ann1.start == 0
        assert ann1.end == 2
        assert len(ann1.features) == 3
        assert ann1.features.get("a") == 1
        assert ann1.features.get("b") == True
        assert ann1.features.get("c") == "some string"
        ann2 = doc1.annset("Set2").first()
        assert ann2.type == "Type2"
        assert ann2.start == 2
        assert ann2.end == 8
        assert len(ann2.features) == 0


class TestFormatJson:
    def test_formatjson01(self):
        from gatenlp.document import Document

        curpath = os.path.abspath(os.path.curdir)
        tstpath = os.path.join(curpath, "tests")
        doc = Document.load(
            source=os.path.join(tstpath, "testdoc1.bdocjs"), fmt="text/bdocjs"
        )
        fs = doc.features
        # print("\n!!!!!!!!!!!!!!!!!!!!!!!! FEATURES=", fs)
        assert "fInt1" in fs and fs["fInt1"] == 222
        assert "fBoolean" in fs and fs["fBoolean"] == True
        assert "fString1" in fs and fs["fString1"] == "Some string"
        assert "fLong1" in fs and fs["fLong1"] == 123
        assert "fFloat1" in fs and fs["fFloat1"] == 3.4
        assert "fComplex1" in fs
        fc1 = fs["fComplex1"]
        assert "key1" in fc1
        assert "fComplex2a" in fs
        assert "fComplex2b" in fs
        assert "feat1" in fs["fComplex2a"]
        assert "feat1" in fs["fComplex2b"]
        fc2a = fs["fComplex2b"]["feat1"]
        fc2b = fs["fComplex2b"]["feat1"]
        assert "k2" in fc2a
        assert "k2" in fc2b
        assert fc2a["k2"] == fc2b["k2"]
        assert fc2a["k2"] is fc2b["k2"]
        anns = doc.annset()
        # print("\n!!!!!!!!!!!!!!!!!!!!!!!! ANNS=", anns)
        assert len(anns) == 2
        ann1, ann2 = list(anns)[0:2]
        assert ann1.type == "Type1"
        assert ann1.start == 0
        assert ann1.end == 4
        assert ann1.id == 0
        assert "fComplex2a" in ann1.features
        assert "k2" in ann1.features["fComplex2a"]
        assert fc2a["k2"] == ann1.features["fComplex2a"]["k2"]
        # json does not preserve identical references
        # assert fc2a["k2"] is ann1.features["fComplex2a"]["k2"]

        assert ann2.type == "Type1"
        assert ann2.start == 5
        assert ann2.end == 8
        assert ann2.id == 1

    def test_formatjson02(self):
        from gatenlp.document import Document

        doc1 = makedoc1()
        asjson = doc1.save_mem(fmt="text/bdocjs")
        doc2 = Document.load_mem(asjson, fmt="text/bdocjs")
        assert doc2.text == DOC1_TEXT
        assert len(doc1.features) == 1
        assert doc1.features.get("feat1") == "value1"
        assert len(doc1.annset()) == 1
        assert len(doc1.annset("Set2")) == 1
        ann1 = doc1.annset().first()
        assert ann1.type == "Type1"
        assert ann1.start == 0
        assert ann1.end == 2
        assert len(ann1.features) == 3
        assert ann1.features.get("a") == 1
        assert ann1.features.get("b") == True
        assert ann1.features.get("c") == "some string"
        ann2 = doc1.annset("Set2").first()
        assert ann2.type == "Type2"
        assert ann2.start == 2
        assert ann2.end == 8
        assert len(ann2.features) == 0


class TestFormatMsgPack:
    def test_formatmsgpack01(self):
        from gatenlp.document import Document

        curpath = os.path.abspath(os.path.curdir)
        tstpath = os.path.join(curpath, "tests")
        doc = Document.load(
            source=os.path.join(tstpath, "testdoc1.bdocmp"), fmt="text/bdocmp"
        )
        fs = doc.features
        # print("\n!!!!!!!!!!!!!!!!!!!!!!!! FEATURES=", fs)
        assert "fInt1" in fs and fs["fInt1"] == 222
        assert "fBoolean" in fs and fs["fBoolean"] == True
        assert "fString1" in fs and fs["fString1"] == "Some string"
        assert "fLong1" in fs and fs["fLong1"] == 123
        assert "fFloat1" in fs and fs["fFloat1"] == 3.4
        assert "fComplex1" in fs
        fc1 = fs["fComplex1"]
        assert "key1" in fc1
        assert "fComplex2a" in fs
        assert "fComplex2b" in fs
        assert "feat1" in fs["fComplex2a"]
        assert "feat1" in fs["fComplex2b"]
        fc2a = fs["fComplex2b"]["feat1"]
        fc2b = fs["fComplex2b"]["feat1"]
        assert "k2" in fc2a
        assert "k2" in fc2b
        assert fc2a["k2"] == fc2b["k2"]
        assert fc2a["k2"] is fc2b["k2"]
        anns = doc.annset()
        # print("\n!!!!!!!!!!!!!!!!!!!!!!!! ANNS=", anns)
        assert len(anns) == 2
        ann1, ann2 = list(anns)[0:2]
        assert ann1.type == "Type1"
        assert ann1.start == 0
        assert ann1.end == 4
        assert ann1.id == 0
        assert "fComplex2a" in ann1.features
        assert "k2" in ann1.features["fComplex2a"]
        assert fc2a["k2"] == ann1.features["fComplex2a"]["k2"]
        # msgpack does not preserve identical references
        # assert fc2a["k2"] is ann1.features["fComplex2a"]["k2"]

        assert ann2.type == "Type1"
        assert ann2.start == 5
        assert ann2.end == 8
        assert ann2.id == 1

    def test_formatmsgpack02(self):
        from gatenlp.document import Document

        doc1 = makedoc1()
        asjson = doc1.save_mem(fmt="text/bdocmp")
        doc2 = Document.load_mem(asjson, fmt="text/bdocmp")
        assert doc2.text == DOC1_TEXT
        assert len(doc1.features) == 1
        assert doc1.features.get("feat1") == "value1"
        assert len(doc1.annset()) == 1
        assert len(doc1.annset("Set2")) == 1
        ann1 = doc1.annset().first()
        assert ann1.type == "Type1"
        assert ann1.start == 0
        assert ann1.end == 2
        assert len(ann1.features) == 3
        assert ann1.features.get("a") == 1
        assert ann1.features.get("b") == True
        assert ann1.features.get("c") == "some string"
        ann2 = doc1.annset("Set2").first()
        assert ann2.type == "Type2"
        assert ann2.start == 2
        assert ann2.end == 8
        assert len(ann2.features) == 0


class TestFormatHtml:
    def test_formathtml01(self):
        from gatenlp.document import Document
        curpath = os.path.abspath(os.path.curdir)
        tstpath = os.path.join(curpath, "tests")
        # use default parser (html.parser)
        doc = Document.load(source=os.path.join(tstpath, "file1.html"))
        assert "some heading" in doc.text
        assert "Some text." in doc.text
        set1 = doc.annset("Original markups")
        assert set1.size == 4

    def test_formathtml02(self):
        from gatenlp.document import Document
        try:
            import lxml
        except:
            # not installed, skip test
            return
        curpath = os.path.abspath(os.path.curdir)
        tstpath = os.path.join(curpath, "tests")
        doc = Document.load(source=os.path.join(tstpath, "file1.html"), parser="lxml")
        assert "some heading" in doc.text
        assert "Some text." in doc.text
        set1 = doc.annset("Original markups")
        assert set1.size == 4

    def test_formathtml03(self):
        from gatenlp.document import Document
        try:
            import html5lib
        except:
            # not installed, skip test
            return
        curpath = os.path.abspath(os.path.curdir)
        tstpath = os.path.join(curpath, "tests")
        doc = Document.load(source=os.path.join(tstpath, "file1.html"), parser="html5lib")
        assert "some heading" in doc.text
        assert "Some text." in doc.text
        set1 = doc.annset("Original markups")
        # html5lib includes a zero length head annotation for the missing head, so one more annotation than
        # other parsers!
        assert set1.size == 5
