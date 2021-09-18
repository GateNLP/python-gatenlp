
from gatenlp import Document, Annotation, Span
from gatenlp.pam.pampac import Context, Location, Result

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
    Pampac,
    Function
)

# Disable:
#   too-many-statements (R0915)
#   import-outside-toplevel (C0415)
# pylint: disable=R0915, C0415


class TestPampac01:

    def test01(self):
        """
        Unit test method (make linter happy)
        """
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
        assert len(ret[0].matches) == 1

        # do this with the match method
        ret = parser(doc, annlist)
        assert isinstance(ret, Success)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 2
        assert loc.ann_location == 1
        assert len(ret[0].matches) == 1

        # this does NOT first advance the annotation index so the annotation start index
        # is at least 2. So it matches the annotation at index 1 which ends at 1 which is
        # BEFORE the text index we have now.
        assert loc == Location(2, 1)
        ret = Ann(name="tmp1", useoffset=False).parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc == Location(1, 2)
        assert len(ret[0].matches) == 1

        # by default we do advance, so we match the last annotation and end up at text
        # position 4 looking for annotation index 5
        loc = Location(2, 1)
        ret = Ann(name="tmp1", useoffset=True).parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc == Location(3, 5)
        assert len(ret[0].matches) == 1

        # Try to fail
        parser = Ann("Token")
        ret = parser(doc, annlist)
        assert isinstance(ret, Failure)

        # Same without a name: should generate the same locations, but no matches
        parser = Ann()
        ret = parser.parse(Location(), ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 2
        assert loc.ann_location == 1
        assert len(ret[0].matches) == 0

        ret = Ann().parse(loc, ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 3
        assert loc.ann_location == 5
        assert len(ret[0].matches) == 0

        parser = AnnAt(name="a2")
        ret = parser.parse(Location(), ctx)
        assert len(ret) == 1
        assert len(ret[0].matches) == 1

        parser = AnnAt(matchtype="all", name="a3")
        ret = parser.parse(Location(), ctx)
        assert len(ret) == 2
        assert len(ret[0].matches) == 1
        assert len(ret[1].matches) == 1

        # Try Rule
        parser = Ann(name="a1")
        tmp = dict(i=0)

        def rhs1(_succ, **_kwargs):
            tmp["i"] = 1

        rule = Call(parser, rhs1)
        ret = rule.parse(Location(), ctx)
        assert len(ret) == 1
        loc = ret[0].location
        assert loc.text_location == 2
        assert loc.ann_location == 1
        assert len(ret[0].matches) == 1
        assert tmp["i"] == 1

        # use the call method instead
        def rhs2(_succ, **_kwargs):
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
        """
        Unit test method (make linter happy)
        """
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
        assert len(ret[0].matches) == 2
        assert ret[0].matches[0]["ann"].id == 2
        assert ret[0].matches[1]["ann"].id == 3

        # match sequence Ann/Ann, take first at each point
        ret = Seq(AnnAt("Ann", name="1"), AnnAt("Ann", name="2")).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].matches) == 2
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3

        # match sequence Ann/Ann, take first at each point, set useoffset=False so we do not skip to the
        # end offset of the previous before matching the next
        # In that case the next ann we match is the second one at offset 0
        ret = Seq(
            AnnAt("Ann", name="1"), AnnAt("Ann", name="2", useoffset=False)
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].matches) == 2
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 1

        # Make sure we get the correct set of annotations at position 0 and 2
        ret = AnnAt("Ann", name="a", matchtype="all").match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 2
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[1].matches[0]["ann"].id == 1
        # ret.pprint()
        ret = AnnAt("Ann", name="a", matchtype="all").match(
            doc, annlist, location=Location(2, 2)
        )
        assert ret.issuccess()
        assert len(ret) == 2
        assert ret[0].matches[0]["ann"].id == 3
        assert ret[1].matches[0]["ann"].id == 4
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
        assert len(ret[0].matches) == 2
        assert len(ret[1].matches) == 2
        assert len(ret[2].matches) == 2
        assert len(ret[3].matches) == 2
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3
        assert ret[1].matches[0]["ann"].id == 0
        assert ret[1].matches[1]["ann"].id == 4
        assert ret[2].matches[0]["ann"].id == 1
        assert ret[2].matches[1]["ann"].id == 3
        assert ret[3].matches[0]["ann"].id == 1
        assert ret[3].matches[1]["ann"].id == 4

    def test03(self):
        """
        Unit test method (make linter happy)
        """
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
        assert len(ret[0].matches) == 3
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3
        assert ret[0].matches[2]["ann"].id == 5

        # Same as before, but with a name, so we should get one additional matches for the whole sequence
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
        assert len(ret[0].matches) == 4
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3
        assert ret[0].matches[2]["ann"].id == 5
        assert ret[0].matches[3]["span"] == Span(0, 6)

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
        assert len(ret[0].matches) == 4
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3
        assert ret[0].matches[2]["ann"].id == 5
        assert ret[0].matches[3]["ann"].id == 8

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
        assert len(ret[0].matches) == 3
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3
        assert ret[0].matches[2]["ann"].id == 7

        # Try a match with min=0 and max=99 that does not succeed
        # single Ann, single result from N
        # this should return an empty list for matches
        ret = N(
            AnnAt("NotThere", name="a1", matchtype="first"),
            min=0,
            max=99,
            select="first",
            matchtype="first",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].matches) == 0

        # Try a match with min=0 and max=99 that does not succeed
        # single Ann, single result from N
        # this should return an empty list for matches
        ret = N(
            AnnAt("Ann", name="a1", matchtype="first"),
            min=0,
            max=99,
            select="first",
            matchtype="first",
        ).match(doc, annlist)
        assert ret.issuccess()
        assert len(ret) == 1
        assert len(ret[0].matches) == 4
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3
        assert ret[0].matches[2]["ann"].id == 5
        assert ret[0].matches[3]["ann"].id == 8

    def test04(self):
        """
        Unit test method (make linter happy)
        """
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
        assert len(ret[0].matches) == 3
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3
        assert ret[0].matches[2]["ann"].id == 5

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
        assert len(ret[0].matches) == 1
        assert len(ret[1].matches) == 1
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[1].matches[0]["ann"].id == 1

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
        assert len(ret[0].matches) == 2
        assert len(ret[1].matches) == 2
        assert len(ret[2].matches) == 2
        assert len(ret[3].matches) == 2
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3
        assert ret[1].matches[0]["ann"].id == 0
        assert ret[1].matches[1]["ann"].id == 4
        assert ret[2].matches[0]["ann"].id == 1
        assert ret[2].matches[1]["ann"].id == 3
        assert ret[3].matches[0]["ann"].id == 1
        assert ret[3].matches[1]["ann"].id == 4

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
        assert len(ret[0].matches) == 1
        assert len(ret[1].matches) == 1
        assert len(ret[2].matches) == 1
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[1].matches[0]["ann"].id == 1
        assert ret[2].matches[0]["ann"].id == 2

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
        assert len(ret[0].matches) == 1
        assert ret[0].matches[0]["ann"].id == 2

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
        assert len(ret[0].matches) == 3
        assert len(ret[1].matches) == 3
        assert len(ret[2].matches) == 3
        assert len(ret[3].matches) == 3
        assert ret[0].matches[0]["ann"].id == 0
        assert ret[0].matches[1]["ann"].id == 3
        assert ret[0].matches[2]["ann"].id == 7
        assert ret[1].matches[0]["ann"].id == 0
        assert ret[1].matches[1]["ann"].id == 4
        assert ret[1].matches[2]["ann"].id == 7
        assert ret[2].matches[0]["ann"].id == 1
        assert ret[2].matches[1]["ann"].id == 3
        assert ret[2].matches[2]["ann"].id == 7
        assert ret[3].matches[0]["ann"].id == 1
        assert ret[3].matches[1]["ann"].id == 4
        assert ret[3].matches[2]["ann"].id == 7

    def test05(self):
        """
        Unit test method (make linter happy)
        """
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
        loc = ctx.inc_location(Location(0, 0), by_offset=1)
        pat1.parse(location=loc, context=ctx)

        def r1_action(succ, _context=None, **_kwargs):
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


class TestPampacRemoveAnn:

    def test01(self):
        """
        Unit test method (make linter happy)
        """
        from gatenlp.pam.pampac.actions import RemoveAnn

        def make_doc():
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
            return doc

        doc = make_doc()

        # match first match of Ann an remove
        assert len(doc.annset()) == 11
        Pampac(
            Rule(
                AnnAt("Ann", name="match", matchtype="all"),
                RemoveAnn("match", doc.annset())
            ),
        ).run(doc, doc.annset().with_type("Ann", "XXX", "Person", "Token"))
        assert len(doc.annset()) == 7


class TestPampacMisc:

    def test01(self):
        """
        Unit test method (make linter happy)
        """
        loc1 = Location(0, 0)
        loc2 = Location(0, 1)
        loc3 = Location(1, 0)
        loc4 = Location(0, 0)

        assert loc1 != loc2
        assert loc1 != loc3
        assert loc1 == loc4
        assert loc1 != "asa"

        assert str(loc1) == "Location(0,0)"

        res1 = Result(location=Location(10, 10), span=Span(4, 10))
        assert list(res1.anns4matches()) == []
        assert res1.matches4name("xxx") == []

        res2 = Result(matches={"span": Span(3, 4), "name": "xx"}, location=Location(12, 12), span=Span(4, 12))
        assert list(res2.anns4matches()) == []
        assert res2.matches4name("xx") == [{"span": Span(3, 4), "name": "xx"}]

        res3 = Result(matches=[{"span": Span(3, 4), "name": "xx"}, {"span": Span(3, 4), "name": "yy"}, ],
                      location=Location(10, 10), span=Span(4, 10))
        assert list(res3.anns4matches()) == []
        assert res3.matches4name("xx") == [{"span": Span(3, 4), "name": "xx"}]

        assert str(res1) == "Result(loc=Location(10,10),span=Span(4,10),nmatches=0)"
        assert res1.__repr__() == "Result(loc=Location(10,10),span=Span(4,10),matches=[])"

        fail1 = Failure()
        assert not fail1.issuccess()
        assert fail1.describe() == """None at ?/?: Parser Error"""

        fail2 = Failure(message="Some problem", parser="Parser1", location=loc1)
        assert fail2.describe() == """Parser1 at 0/0: Some problem"""

        fail3 = Failure(message="Another problem", parser="Parser2", location=loc1, causes=[fail2, fail1])
        assert fail3.describe() == """Parser2 at 0/0: Another problem
Caused by:
    Parser1 at 0/0: Some problem
    None at ?/?: Parser Error"""
        #
        doc1 = Document("somedoc")
        set1 = doc1.annset()
        ctx1 = Context(doc1, set1)
        assert ctx1.annset.size == 0
        assert ctx1.get_ann(loc1) is None

        succ1 = Success(res1, ctx1)
        assert succ1.issuccess()
        assert succ1.select_result([res1, res2]) == res1
        assert succ1.select_result([res1, res2], matchtype="all") == [res1, res2]
        assert succ1.select_result([res1, res2], matchtype="longest") == res2
        assert succ1.select_result([res1, res2], matchtype="shortest") == res1
        assert succ1.result(matchtype="first") == res1
        for r in succ1:
            assert isinstance(r, Result)
        assert succ1[0] == res1

    def test02(self):
        """
        Unit test method (make linter happy)
        """

        def fun1(location, context):
            return location, context

        parser1 = Function(fun1)
        assert parser1.parse(1, 2) == (1, 2)
