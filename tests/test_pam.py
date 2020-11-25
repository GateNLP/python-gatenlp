import os
from gatenlp import Document, Annotation, Span
from gatenlp.pam.pampac import Context, Location

from gatenlp.pam.pampac import (
    Ann,
    AnnAt,
    Call,
    Find,
    Text,
    N,
    Seq,
    Or,
    Success,
    Failure,
    Rule,
    Pampac
)


class TestPampac01:
    def test01(self):
        doc = Document("Some test document")
        doc.annset().add(0, 2, "Ann")
        doc.annset().add(0, 1, "Ann")
        doc.annset().add(1, 2, "Ann")
        doc.annset().add(1, 2, "Token")
        doc.annset().add(2, 3, "Ann")
        annlist = list(doc.annset())

        ctx = Context(doc, annlist)
        parser = Ann(name="a1")
        ret = parser.parse(Location(), ctx)
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
        assert loc == Location(2, 1)
        ret = Ann(name="tmp1", useoffset=False).parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc == Location(1, 2)
        assert len(ret[0].data) == 1

        # by default we do advance, so we match the last annotation and end up at text
        # position 4 looking for annotation index 5
        loc = Location(2, 1)
        ret = Ann(name="tmp1", useoffset=True).parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc == Location(3, 5)
        assert len(ret[0].data) == 1

        # Try to fail
        parser = Ann("Token")
        ret = parser(doc, annlist)
        assert isinstance(ret, Failure)

        # Same without a name: should generate the same locations, but no data
        parser = Ann()
        ret = parser.parse(Location(), ctx)
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
        ret = parser.parse(Location(), ctx)
        assert len(ret) == 1
        assert len(ret[0].data) == 1

        parser = AnnAt(matchtype="all", name="a3")
        ret = parser.parse(Location(), ctx)
        assert len(ret) == 2
        assert len(ret[0].data) == 1
        assert len(ret[1].data) == 1

        # Try Rule
        parser = Ann(name="a1")
        tmp = dict(i=0)

        def rhs1(succ, **kwargs):
            tmp["i"] = 1

        rule = Call(parser, rhs1)
        ret = rule.parse(Location(), ctx)
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
        ret = parser.parse(Location(), ctx)
        print(ret)
        assert tmp["i"] == 2

        parser = Find(AnnAt(type="Token", name="at"), by_anns=False)
        ret = parser.parse(Location(), ctx)
        print(ret)

        parser = Find(AnnAt(type="Token", name="at"), by_anns=True)
        ret = parser.parse(Location(), ctx)
        print(ret)

        parser = Find(Text("document", name="t1"), by_anns=False)
        ret = parser.parse(Location(), ctx)
        print(ret)

        parser = Seq(Ann("Ann", name="a1"), Ann("Ann", name="a2"), matchtype="longest")
        ret = parser.parse(Location(), ctx)
        print(ret)

        parser = N(AnnAt("Ann", name="a1"), 1, 5, matchtype="first")
        ret = parser.parse(Location(), ctx)
        print(ret)

        parser = Or(Ann("X", name="x1"), Ann("Ann", name="a1"))
        ret = parser.parse(Location(), ctx)
        print(ret)

        parser = Ann("X", name="x1") | Ann("Y", name="y1") | Ann("Ann", name="a1")
        ret = parser.parse(Location(), ctx)
        print(ret)

        parser = Ann("Ann", name="a1") >> Ann("Ann", name="a2")
        ret = parser.parse(Location(), ctx)
        print(ret)

        parser = Ann("Ann", name="a1") * 2
        ret = parser.parse(Location(), ctx)
        print(ret)

        parser = Ann("Ann", name="a1") * (1, 3)
        ret = parser.parse(Location(), ctx)
        print(ret)

    def test02(self):
        # Test multiple result matches

        doc = Document("Some test document")
        doc.annset().add(0, 2, "Ann")  # 0
        doc.annset().add(0, 2, "Ann")  # 1
        doc.annset().add(0, 2, "Token")  # 2
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
        ret = Seq(
            AnnAt("Ann", name="1"), AnnAt("Ann", name="2", useoffset=False)
        ).match(doc, annlist)
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
        ret = AnnAt("Ann", name="a", matchtype="all").match(
            doc, annlist, location=Location(2, 2)
        )
        assert ret.issuccess()
        assert len(ret) == 2
        assert ret[0].data[0]["ann"].id == 3
        assert ret[1].data[0]["ann"].id == 4
        # ret.pprint()

        # Match sequence of two anns in order, take all results
        ret = Seq(
            AnnAt("Ann", name="1", matchtype="all"),
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

    def test03(self):
        # Test single result matches with N, with and without the until clause

        doc = Document("Some test document")
        doc.annset().add(0, 2, "Ann")  # 0
        doc.annset().add(0, 2, "Ann")  # 1
        doc.annset().add(0, 2, "Token")  # 2
        doc.annset().add(2, 4, "Ann")  # 3
        doc.annset().add(2, 4, "Ann")  # 4
        doc.annset().add(4, 6, "Ann")  # 5
        doc.annset().add(4, 6, "Ann")  # 6
        doc.annset().add(4, 6, "Person")  # 7
        doc.annset().add(6, 8, "Ann")  # 8
        doc.annset().add(6, 8, "Ann")  # 9
        doc.annset().add(8, 10, "XXXX")  # 10
        annlist = list(doc.annset())

        # single Ann, single result from N
        # this should return annotation ids 0, 3, 5
        ret = N(
            AnnAt("Ann", name="a1", matchtype="first"),
            min=2,
            max=3,
            select="first",
            matchtype="first",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 3
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 3
        assert ret[0].data[2]["ann"].id == 5

        # Same as before, but with a name, so we should get one additional data for the whole sequence
        # with a span
        ret = N(
            AnnAt("Ann", name="a1", matchtype="first"),
            min=2,
            max=3,
            select="first",
            matchtype="first",
            name="n1"
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 4
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 3
        assert ret[0].data[2]["ann"].id == 5
        assert ret[0].data[3]["span"] == Span(0, 6)

        # single Ann, single result from N
        # this should return annotation ids 0, 3, 5, 8
        ret = N(
            AnnAt("Ann", name="a1", matchtype="first"),
            min=2,
            max=99,
            select="first",
            matchtype="first",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 4
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 3
        assert ret[0].data[2]["ann"].id == 5
        assert ret[0].data[3]["ann"].id == 8

        # single Ann, single result from N, with early stopping at Person
        # this should return annotation ids 0, 3, 7
        ret = N(
            AnnAt("Ann", name="a1", matchtype="first"),
            until=AnnAt("Person", name="p"),
            min=2,
            max=99,
            select="first",
            matchtype="first",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 3
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 3
        assert ret[0].data[2]["ann"].id == 7

        # Try a match with min=0 and max=99 that does not succeed
        # single Ann, single result from N
        # this should return an empty list for data
        ret = N(
            AnnAt("NotThere", name="a1", matchtype="first"),
            min=0,
            max=99,
            select="first",
            matchtype="first",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 0

        # Try a match with min=0 and max=99 that does not succeed
        # single Ann, single result from N
        # this should return an empty list for data
        ret = N(
            AnnAt("Ann", name="a1", matchtype="first"),
            min=0,
            max=99,
            select="first",
            matchtype="first",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 4
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 3
        assert ret[0].data[2]["ann"].id == 5
        assert ret[0].data[3]["ann"].id == 8

    def test04(self):
        # Test multiple result matches with N, with and without the until clause

        doc = Document("Some test document")
        doc.annset().add(0, 2, "Ann")  # 0
        doc.annset().add(0, 2, "Ann")  # 1
        doc.annset().add(0, 2, "Token")  # 2
        doc.annset().add(2, 4, "Ann")  # 3
        doc.annset().add(2, 4, "Ann")  # 4
        doc.annset().add(4, 6, "Ann")  # 5
        doc.annset().add(4, 6, "Ann")  # 6
        doc.annset().add(4, 6, "Person")  # 7
        doc.annset().add(6, 8, "Ann")  # 8
        doc.annset().add(6, 8, "Ann")  # 9
        doc.annset().add(8, 10, "XXXX")  # 10
        annlist = list(doc.annset())

        # multiple Anns, single result from N: first
        # This should find 0,3,5
        ret = N(
            AnnAt("Ann", name="a1", matchtype="all"),
            min=2,
            max=3,
            select="all",
            matchtype="first",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 3
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 3
        assert ret[0].data[2]["ann"].id == 5

        # multiple Anns, all results from N
        # should return 0,1
        ret = N(
            AnnAt("Ann", name="a1", matchtype="all"),
            min=1,
            max=1,
            select="all",
            matchtype="all",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 2
        assert len(ret[0].data) == 1
        assert len(ret[1].data) == 1
        assert ret[0].data[0]["ann"].id == 0
        assert ret[1].data[0]["ann"].id == 1

        # multiple Anns, all results from N
        ret = N(
            AnnAt("Ann", name="a1", matchtype="all"),
            min=1,
            max=2,
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

        # multiple Anns, all results from N
        # just three for the first ann: 0,1,2
        ret = N(
            AnnAt(name="a1", matchtype="all"),
            min=1,
            max=1,
            select="all",
            matchtype="all",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 3
        assert len(ret[0].data) == 1
        assert len(ret[1].data) == 1
        assert len(ret[2].data) == 1
        assert ret[0].data[0]["ann"].id == 0
        assert ret[1].data[0]["ann"].id == 1
        assert ret[2].data[0]["ann"].id == 2

        # This should just find the Token as the first and only match!
        ret = N(AnnAt("Ann", name="a1", matchtype="all"),
                until=AnnAt("Token", name="t", matchtype="first"),
                min=0,
                max=3,
                select="all",
                matchtype="all"
                ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].data) == 1
        assert ret[0].data[0]["ann"].id == 2


        # This should terminate with Person and find all paths that can lead up to PErson:
        # 0,3 0,4 1,3 1,4
        ret = N(AnnAt("Ann", name="a1", matchtype="all"),
                until=AnnAt("Person", name="t", matchtype="first"),
                min=1,
                max=3,
                select="all",
                matchtype="all"
                ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 4
        assert len(ret[0].data) == 3
        assert len(ret[1].data) == 3
        assert len(ret[2].data) == 3
        assert len(ret[3].data) == 3
        assert ret[0].data[0]["ann"].id == 0
        assert ret[0].data[1]["ann"].id == 3
        assert ret[0].data[2]["ann"].id == 7
        assert ret[1].data[0]["ann"].id == 0
        assert ret[1].data[1]["ann"].id == 4
        assert ret[1].data[2]["ann"].id == 7
        assert ret[2].data[0]["ann"].id == 1
        assert ret[2].data[1]["ann"].id == 3
        assert ret[2].data[2]["ann"].id == 7
        assert ret[3].data[0]["ann"].id == 1
        assert ret[3].data[1]["ann"].id == 4
        assert ret[3].data[2]["ann"].id == 7


    def test05(self):
        # Rules and Pampac

        doc = Document("Some test document")
        doc.annset().add(0, 2, "Ann1")  # 0
        doc.annset().add(2, 4, "Ann2")  # 1
        doc.annset().add(3, 5, "Ann2")  # 2
        doc.annset().add(4, 5, "Ann2")  # 3
        doc.annset().add(8, 10, "Ann2")  # 4
        annset = doc.annset()
        orig_len = len(annset)
        annlist = list(doc.annset())

        # first make sure the pattern works as we want
        ctx = Context(doc=doc, anns=annlist)
        pat1 = AnnAt("Ann2", name="a1") >> AnnAt("Ann2", name="a2")
        loc = ctx.inc_location(Location(0,0), by_offset=1)
        ret = pat1.parse(location=loc, context=ctx)

        def r1_action(succ, context=None, **kwargs):
            span = succ[0].span
            ann = succ.context.outset.add(span.start, span.end, "NEW")
            return ann
        r1 = Rule(
            AnnAt("Ann2") >> AnnAt("Ann2"),
            r1_action
        )
        pampac = Pampac(r1)
        pampac.set_skip = "longest"
        pampac.set_select = "first"
        outset = doc.annset()
        ret = pampac.run(doc, annlist, outset=outset, debug=True)
        assert len(ret) == 1
        assert len(ret[0]) == 2
        idx, retlist = ret[0]
        assert idx == 1
        assert len(retlist) == 1
        a = retlist[0]
        assert isinstance(a, Annotation)
        assert a.start == 2
        assert a.end == 5
        assert a.type == "NEW"
        assert len(outset) == orig_len + 1


if __name__ == "__main__":
    TestPampac01().test05()
