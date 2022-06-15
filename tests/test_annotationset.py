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

def make_doc2():
    doc = Document("0123456789")
    annset = doc.annset()
    for i in range(10):
        annset.add(i, i + 1, f"ANN{i}")
    return doc

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


class TestAnnotationSetRels:

    def test_annotationset_rels01(self):
        """
        Unit test method (make linter happy)
        """
        doc = make_doc()
        set1 = doc.annset("set1")
        ann1 = set1.with_type("Ann1").for_idx(0)
        ann2 = set1.with_type("Ann2").for_idx(0)
        ann3 = set1.with_type("Ann3").for_idx(0)
        ann4 = set1.with_type("Ann4").for_idx(0)
        ann5 = set1.with_type("Ann5").for_idx(0)
        _ann6 = set1.with_type("Ann6").for_idx(0)
        ann7 = set1.with_type("Ann7").for_idx(0)
        _ann8 = set1.with_type("Ann8").for_idx(0)
        ann9 = set1.with_type("Ann9").for_idx(0)
        _ann10 = set1.with_type("Ann10").for_idx(0)
        ann11 = set1.with_type("Ann11").for_idx(0)
        ann12 = set1.with_type("Ann12").for_idx(0)

        assert set1.changelog is None
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
        # the annotation itself is checked by object!
        # == is checked by object, .equal() is checked by content
        for ann in set1:
            assert ann not in set2
            assert ann.id in set2
            assert set2.get(ann.id).equal(ann)
            assert not set2.get(ann.id) == ann
        for ann in set2:
            assert ann not in set1
            assert ann.id in set1
            assert set1.get(ann.id).equal(ann)
            assert not set1.get(ann.id) == ann

        s1 = set1.within(ann1)
        assert len(s1) == 9

        s1 = set1.within(ann11)
        assert len(s1) == 1

        set1.clear()
        assert len(set1) == 0

    def test_overlapping1(self):
        doc = Document("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        set1 = doc.annset("set1")
        set2 = doc.annset("set2")
        ann1 = set1.add(13, 17, "sometype")
        ann2 = set2.add(16, 17, "sometype")
        ret = set1.overlapping(ann2, include_self=True)
        assert len(ret) == 1

    def test_annotationset_exps(self):
        """
        Unit test method (make linter happy)
        """
        import pytest
        doc = Document("some doc")
        annset = doc.annset()
        with pytest.raises(Exception) as ex:
            start = annset.start
        assert str(ex.value)

    def test_annotationset_misc01(self):
        """
        Unit test method (make linter happy)
        """
        doc = Document("some doc")
        # add two annotations to set A, with ids 0 and 1
        a1 = doc.annset("A").add(0, 1, "A1")
        a2 = doc.annset("A").add(0, 2, "A2")
        # add two annotations to set B, also with ids 0 and 1
        b1 = doc.annset("B").add(0, 1, "B1")
        b2 = doc.annset("B").add(0, 2, "B2")
        # get all annotations in set A within annotation A2: should be a1  (include_self is False by default)
        tmpset = doc.annset("A").within(a2)
        assert len(tmpset) == 1
        assert a1 in tmpset
        # same but with include_self is True
        tmpset = doc.annset("A").within(a2, include_self=True)
        assert len(tmpset) == 2
        assert a1 in tmpset
        assert a2 in tmpset
        # same but use annotation b2: for this, we should always get both a1 and a2
        tmpset = doc.annset("A").within(b2, include_self=False)
        assert len(tmpset) == 2
        assert a1 in tmpset
        assert a2 in tmpset
        tmpset = doc.annset("A").within(b2, include_self=True)
        assert len(tmpset) == 2
        assert a1 in tmpset
        assert a2 in tmpset




class TestAnnotationSetEdit:

    def test_annotationset_edit01(self):
        doc = make_doc2()
        annset = doc.annset()
        annset._edit([(2, 5, "")], affected_strategy="delete_all")
        assert len(annset) == 7
        for idx, n in enumerate(["ANN0", "ANN1", "ANN5", "ANN6", "ANN7", "ANN8", "ANN9"]):
            anns = list(annset.with_type(n))
            assert len(anns) == 1
            ann = anns[0]
            assert ann.start == idx
            assert ann.end == idx + 1
        for idx, n in enumerate(["ANN2", "ANN3", "ANN4"]):
            anns = list(annset.with_type(n))
            assert len(anns) == 0

    def test_annotationset_edit02(self):
        doc = make_doc2()
        annset = doc.annset()
        annset._edit([(2, 5, "aaaaa")], affected_strategy="delete_all")
        assert len(annset) == 7
        for idx, n in enumerate(["ANN0", "ANN1", "ANN5", "ANN6", "ANN7", "ANN8", "ANN9"]):
            anns = list(annset.with_type(n))
            assert len(anns) == 1
            ann = anns[0]
            if idx < 2:
                assert ann.start == idx
                assert ann.end == idx + 1
            else:
                assert ann.start == idx + 3 + 2
                assert ann.end == idx + 3 + 2 + 1
        for idx, n in enumerate(["ANN2", "ANN3", "ANN4"]):
            anns = list(annset.with_type(n))
            assert len(anns) == 0

    def test_annotationset_edit10(self):
        doc = make_doc2()
        annset = doc.annset()
        annset._edit([(2, 5, "")], affected_strategy="adapt")
        assert len(annset) == 10
        for idx, n in enumerate(["ANN0", "ANN1", "ANN5", "ANN6", "ANN7", "ANN8", "ANN9"]):
            anns = list(annset.with_type(n))
            assert len(anns) == 1
            ann = anns[0]
            assert ann.start == idx
            assert ann.end == idx + 1
        for idx, n in enumerate(["ANN2", "ANN3", "ANN4"]):
            anns = list(annset.with_type(n))
            assert len(anns) == 1
            ann = anns[0]
            assert ann.start == 2
            assert ann.end == 2

