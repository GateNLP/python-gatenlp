
import os
from gatenlp import Document, Annotation
from gatenlp.pam.pampac import Context, ParseLocation

from gatenlp.pam.pampac import Ann, AnnAt, Call, Find, Text, N, Seq, Or, Success, Failure

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
        assert isinstance(ret, Success)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 2
        assert loc.ann_location == 1
        assert len(ret[0].data) == 1

        # do this with the match method
        ret = parser(doc, annlist)
        assert isinstance(ret, Success)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 2
        assert loc.ann_location == 1
        assert len(ret[0].data) == 1

        # this does NOT first advance the annotation index so the annotation start index
        # is at least 2. So it matches the annotation at index 1 which ends at 1 which is
        # BEFORE the text index we have now.
        assert loc == ParseLocation(2, 1)
        ret = Ann(name="tmp1", useoffset=False).parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc == ParseLocation(1, 2)
        assert len(ret[0].data) == 1

        # by default we do advance, so we match the last annotation and end up at text
        # position 4 looking for annotation index 5
        loc = ParseLocation(2, 1)
        ret = Ann(name="tmp1", useoffset=True).parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc == ParseLocation(3, 5)
        assert len(ret[0].data) == 1


        # Try to fail
        parser = Ann("Token")
        ret = parser(doc, annlist)
        assert isinstance(ret, Failure)

        # Same without a name: should generate the same locations, but no data
        parser = Ann()
        ret = parser.parse(ParseLocation(), ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 2
        assert loc.ann_location == 1
        assert len(ret[0].data) == 0

        ret = Ann().parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 3
        assert loc.ann_location == 5
        assert len(ret[0].data) == 0

        parser = AnnAt(name="a2")
        ret = parser.parse(ParseLocation(), ctx)
        assert len(ret) == 1
        assert len(ret[0].data) == 1

        parser = AnnAt(matchtype="all", name="a3")
        ret = parser.parse(ParseLocation(), ctx)
        assert len(ret) == 2
        assert len(ret[0].data) == 1
        assert len(ret[1].data) == 1

        # Try Rule
        parser = Ann(name="a1")
        tmp = dict(i=0)
        def rhs1(succ, **kwargs):
            tmp["i"] = 1
        rule = Call(parser, rhs1)
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

        parser = Ann("Ann", name="a1") * 2
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

        parser = Ann("Ann", name="a1") * (1,3)
        ret = parser.parse(ParseLocation(), ctx)
        print(ret)

    def test02(self):
        # Test multiple result matches

        doc = Document("Some test document")
        doc.annset().add(0, 2, "Ann")  # 0
        doc.annset().add(0, 2, "Ann")  # 1
        doc.annset().add(0, 2, "Token") # 2
        doc.annset().add(2, 4, "Ann")  # 3
        doc.annset().add(2, 4, "Ann")  # 4
        annlist = list(doc.annset())

        # match all annotations at the document start
        ret = AnnAt(matchtype="all").match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 3

        # match sequence Token/Ann, take first at each point
        # this should match annotation ids 2 and 3
        ret = Seq(AnnAt("Token", name="1"), AnnAt("Ann", name="2")).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 2
        assert ret[0].data[0]["ann"].id == 2
        assert ret[0].data[1]["ann"].id == 3

        # match sequence Ann/Ann, take first at each point
        ret = Seq(AnnAt("Ann", name="1"), AnnAt("Ann", name="2")).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 2
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 3

        # match sequence Ann/Ann, take first at each point, set useoffset=False so we do not skip to the
        # end offset of the previous before matching the next
        # In that case the next ann we match is the second one at offset 0
        ret = Seq(AnnAt("Ann", name="1"), AnnAt("Ann", name="2", useoffset=False)).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 2
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 1

        # Make sure we get the correct set of annotations at position 0 and 2
        ret = AnnAt("Ann", name="a", matchtype="all").match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 2
        assert ret[0].data[0]["ann"].id == 0
        assert ret[1].data[0]["ann"].id == 1
        # ret.pprint()
        ret = AnnAt("Ann", name="a", matchtype="all").match(doc, annlist, location=ParseLocation(2,2))
        assert ret.issuccess()
        assert len(ret) == 2
        assert ret[0].data[0]["ann"].id == 3
        assert ret[1].data[0]["ann"].id == 4
        # ret.pprint()

        # Match sequence of two anns in order, take all results
        ret = Seq(AnnAt("Ann", name="1", matchtype="all"),
                  AnnAt("Ann", name="2", matchtype="all"),
                  select="all",
                  matchtype="all",
                  ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 4
        assert len(ret[0].data) == 2
        assert len(ret[1].data) == 2
        assert len(ret[2].data) == 2
        assert len(ret[3].data) == 2
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 3
        assert ret[1].data[0]["ann"].id == 0
        assert ret[1].data[1]["ann"].id == 4
        assert ret[2].data[0]["ann"].id == 1
        assert ret[2].data[1]["ann"].id == 3
        assert ret[3].data[0]["ann"].id == 1
        assert ret[3].data[1]["ann"].id == 4

if __name__ == "__main__":
    TestPampac01().test01()