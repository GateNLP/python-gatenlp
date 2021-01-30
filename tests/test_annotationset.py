"""
Module for testing the AnnotationSet API.
"""

from gatenlp import Document, AnnotationSet, Span


def make_doc():
    doc = Document("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
    set1 = doc.annset("set1")
    # starting positions:
    # 0: Ann2
    # 3: Ann1, Ann10
    # 12: Ann5
    # 18: Ann3, Ann7, Ann9, Ann11
    # 24: Ann6, Ann8
    # 36: Ann12
    # 39: Ann4
    set1.add(3, 42, "Ann1")
    set1.add(0, 6, "Ann2")
    set1.add(18, 24, "Ann3")
    set1.add(39, 45, "Ann4")
    set1.add(12, 18, "Ann5")
    set1.add(24, 30, "Ann6")
    set1.add(18, 18, "Ann7")
    set1.add(24, 24, "Ann8")
    set1.add(18, 24, "Ann9")
    set1.add(3, 9, "Ann10")
    set1.add(18, 18, "Ann11")
    set1.add(36, 42, "Ann12")
    return doc


class TestAnnotationSetRels:

    def test_annotationset_rels01(self):
        doc = make_doc()
        set1 = doc.annset("set1")
        ann1 = set1.with_type("Ann1").for_idx(0)
        ann2 = set1.with_type("Ann2").for_idx(0)
        ann3 = set1.with_type("Ann3").for_idx(0)
        ann4 = set1.with_type("Ann4").for_idx(0)
        ann5 = set1.with_type("Ann5").for_idx(0)
        ann6 = set1.with_type("Ann6").for_idx(0)
        ann7 = set1.with_type("Ann7").for_idx(0)
        ann8 = set1.with_type("Ann8").for_idx(0)
        ann9 = set1.with_type("Ann9").for_idx(0)
        ann10 = set1.with_type("Ann10").for_idx(0)
        ann11 = set1.with_type("Ann11").for_idx(0)
        ann12 = set1.with_type("Ann12").for_idx(0)

        assert set1.changelog == None
        assert set1.document == doc
        assert set1.end == 45
        assert not set1.immutable
        assert set1.length == 45
        assert set1.name == "set1"
        assert set1.size == 12
        assert set1.span == Span(0, 45)
        assert set1.start == 0
        tnames = set1.type_names
        assert len(tnames) == 12
        assert ann1 in set1
        assert ann2 in set1
        assert ann12 in set1
        a1 = set1.get(0)
        assert a1 == ann1
        annlist1 = list(set1)
        assert len(annlist1) == 12
        assert annlist1[0] == ann2
        assert annlist1[11] == ann4

        s_after_ann2 = set1.after(ann2)
        assert len(s_after_ann2) == 9
        assert ann3 in s_after_ann2
        assert ann11 in s_after_ann2

        s_after_ann5a = set1.after(ann5, immediately=True)
        assert len(s_after_ann5a) == 4
        s_after_ann5b = set1.after(ann5, immediately=False)
        assert len(s_after_ann5b) == 8

        s_after_ann7a = set1.after(ann7, immediately=True)
        assert len(s_after_ann7a) == 3

        s_before_ann3a = set1.before(ann3, immediately=True)
        assert len(s_before_ann3a) == 3
        assert ann5 in s_before_ann3a
        assert ann7 in s_before_ann3a
        assert ann11 in s_before_ann3a

        s_before_ann3b = set1.before(ann3)
        assert len(s_before_ann3b) == 5

        l1 = list(set1.by_offset())
        assert len(l1) == 7

        l2 = list(set1.by_span())
        assert len(l2) == 10

        s1 = set1.coextensive(ann2)
        assert len(s1) == 0
        s1 = set1.coextensive(ann3)
        assert len(s1) == 1
        s1 = set1.coextensive(ann3.span)
        assert len(s1) == 2
        assert ann3 in s1
        assert ann9 in s1

        s1 = set1.covering(ann3)
        assert len(s1) == 2
        assert ann1 in s1
        assert ann9 in s1

        s1 = set1.covering(ann11)
        assert len(s1) == 4
        assert ann1 in s1
        assert ann3 in s1
        assert ann7 in s1
        assert ann9 in s1

        s1 = set1.detach()
        assert s1.immutable
        assert s1.isdetached()
        assert len(s1) == len(set1)
        for ann in set1:
            assert ann in s1

        l1 = list(set1.fast_iter())
        assert len(l1) == 12
        assert l1[0] == ann1
        assert l1[1] == ann2
        assert l1[11] == ann12

        a1 = set1.first()
        assert a1 == ann2
        a1 = set1.last()
        assert a1 == ann4

        a1 = set1.get(0)
        assert a1 == ann1
        a1 = set1.get(1)
        assert a1 == ann2

        s1 = set1.overlapping(ann1)
        assert len(s1) == 11
        s1 = set1.overlapping(ann11)
        assert len(s1) == 4
        assert ann1 in s1
        assert ann3 in s1
        assert ann7 in s1
        assert ann9 in s1
        s1 = set1.overlapping(ann3)
        assert len(s1) == 4
        assert ann1 in s1
        assert ann7 in s1
        assert ann9 in s1
        assert ann11 in s1
        s1 = set1.overlapping(ann7)
        assert len(s1) == 4
        assert ann1 in s1
        assert ann3 in s1
        assert ann9 in s1
        assert ann11 in s1

        l1 = list(set1.reverse_iter())
        assert len(l1) == 12
        assert l1[0] == ann4
        assert l1[11] == ann2

        s1 = set1.start_ge(ann3.start)
        assert len(s1) == 8

        s1 = set1.start_lt(ann3.start)
        assert len(s1) == 4

        s1 = set1.start_min_ge(ann3.start+1)
        assert len(s1) == 2

        s1 = set1.startingat(ann3)
        assert len(s1) == 3

        s1 = set1.startingat(ann3.start)
        assert len(s1) == 4

        dict1 = set1.to_dict()
        set2 = AnnotationSet.from_dict(dict1)
        assert set1.size == set2.size
        for ann in set1:
            assert ann in set2
        for ann in set2:
            assert ann in set1

        s1 = set1.within(ann1)
        assert len(s1) == 9

        s1 = set1.within(ann11)
        assert len(s1) == 1

        set1.clear()
        assert len(set1) == 0



    def test_annotationset_exps(self):
        import pytest
        # with pytest.raises(Exception) as ex:
        #     Annotation(3, 2, "X")
        # assert str(ex.value).startswith("Cannot create annotation")
        pass

    def test_annotationset_misc01(self):
        # TODO: set1.add_ann(ann, annid=None)
        pass
