
import os
from gatenlp import Document, Annotation
from gatenlp.pam.pampac import Context, ParseLocation

from gatenlp.pam.pampac import Ann, AnnAt, Rule, Find, Text, N, Seq, Or

class TestPampac01:

    def test01(self):
        doc = Document("Some test document")
        doc.annset().add(0, 2,"Ann")
        doc.annset().add(0, 1,"Ann")
        doc.annset().add(1, 2, "Ann")
        doc.annset().add(1, 2, "Token")
        doc.annset().add(2, 3, "Ann")
        annlist = list(doc.annset())

        ctx = Context(doc, annlist)
        parser = Ann(name="a1")
        ret = parser.parse(ParseLocation(), ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 2
        assert loc.ann_location == 1
        assert len(ret[0].data) == 1

        ret = parser.parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 1
        assert loc.ann_location == 2
        assert len(ret[0].data) == 1

        # Same without a name: should generate the same locations, but no data
        parser = Ann()
        ret = parser.parse(ParseLocation(), ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 2
        assert loc.ann_location == 1
        assert len(ret[0].data) == 0

        ret = parser.parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 1
        assert loc.ann_location == 2
        assert len(ret[0].data) == 0

        parser = AnnAt(name="a2")
        ret = parser.parse(ParseLocation(), ctx)
        assert len(ret) == 1
        assert len(ret[0].data) == 1

        parser = AnnAt(matchtype="all", name="a3")
        ret = parser.parse(ParseLocation(), ctx)
        assert len(ret) == 1
        assert len(ret[0].data) == 2

        # Try Rule
        parser = Ann(name="a1")
        tmp = dict(i=0)
        def rhs1(succ, **kwargs):
            tmp["i"] = 1
        rule = Rule(parser, rhs1)
        ret = rule.parse(ParseLocation(), ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 2
        assert loc.ann_location == 1
        assert len(ret[0].data) == 1
        assert tmp["i"] == 1

        # use the call method instead
        def rhs2(succ, **kwargs):
            tmp["i"] = 2
        parser = Ann(name="a1").call(rhs2)
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)
        assert tmp["i"] == 2

        parser = Find(AnnAt(type="Token", name="at"), by_anns=False)
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

        parser = Find(AnnAt(type="Token", name="at"), by_anns=True)
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

        parser = Find(Text("document", name="t1"), by_anns=False)
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

        parser = Seq(Ann("Ann", name="a1"), Ann("Ann", name="a2"), matchtype="longest")
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

        parser = N(AnnAt("Ann", name="a1"), 1, 5, matchtype="first")
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

        parser = Or(Ann("X", name="x1"), Ann("Ann", name="a1"))
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

        parser = Ann("X", name="x1") | Ann("Y", name="y1") | Ann("Ann", name="a1")
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

        parser = Ann("Ann", name="a1") >> Ann("Ann", name="a2")
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

if __name__ == "__main__":
    TestPampac01().test01()