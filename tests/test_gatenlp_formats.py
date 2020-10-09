import sys
import os
import pytest


class TestFormatGateXml:

    def test_formatgatexml01(self):
        from gatenlp.document import Document
        curpath = os.path.abspath(os.path.curdir)
        tstpath = os.path.join(curpath, "tests")
        with pytest.raises(Exception) as ex:
            Document.load(source=os.path.join(tstpath, "testdoc1.xml"), fmt="gatexml")
        assert "Unsupported serialization type" in str(ex.value)
        doc = Document.load(source=os.path.join(tstpath, "testdoc1.xml"),
                            fmt="gatexml", ignore_unknown_types=True)
        fs = doc.features
        #print("\n!!!!!!!!!!!!!!!!!!!!!!!! FEATURES=", fs)
        assert "fInt1" in fs and fs["fInt1"] == 222
        assert "fBoolean" in fs and fs["fBoolean"] == True
        assert "fString1" in fs and fs["fString1"] == "Some string"
        assert "fLong1" in fs and fs["fLong1"] == 123
        assert "fFloat1" in fs and fs["fFloat1"] == 3.4
        anns = doc.annset()
        #print("\n!!!!!!!!!!!!!!!!!!!!!!!! ANNS=", anns)
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
        doc = Document.load(source=os.path.join(tstpath, "testdoc1.bdocym"), fmt="text/bdocym")
        fs = doc.features
        #print("\n!!!!!!!!!!!!!!!!!!!!!!!! FEATURES=", fs)
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
        #print("\n!!!!!!!!!!!!!!!!!!!!!!!! ANNS=", anns)
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


