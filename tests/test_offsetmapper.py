import sys


class TestOffsetMapper01:
    def test_offsetmapper01m01(self):
        """
        Unit test method (make linter happy)
        """
        from gatenlp.document import OffsetMapper, Document

        c_poo = "\U0001F4A9"
        c_bridge = "\U0001f309"
        doc1 = Document("01" + c_poo + "3" + c_bridge + c_bridge + c_bridge + "7")
        assert len(doc1) == 8
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

    def test_offsetmapper01m02(self):
        """
        Unit test method (make linter happy)
        """
        # test identical offsets
        from gatenlp.document import OffsetMapper, Document
        doc1 = Document("Just some sample document")
        om1 = OffsetMapper(doc1)
        for idx in range(len(doc1)):
            assert idx == om1.convert_to_java(idx)
            assert idx == om1.convert_to_python(idx)

