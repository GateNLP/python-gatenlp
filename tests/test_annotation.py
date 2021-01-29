"""
Module for testing the Annotation API.
"""

from gatenlp import Document, Annotation, Span


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


class TestAnnotationRels:

    def test_annotation_rels01(self):
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

        assert ann1.iscovering(ann1)
        assert ann1.iscovering(ann1.start)
        assert ann1.iscovering(ann1.end-1)

        assert ann1.isoverlapping(ann2)
        assert ann1.isrightoverlapping(ann1)
        assert ann1.iscovering(ann3)
        assert not ann1.iscovering(ann2)
        assert ann1.isendingwith(ann12)
        assert not ann1.isafter(ann2)
        assert ann1.isstartingat(ann10)
        assert ann1.iscovering(ann5)
        assert ann1.iscovering(ann7)
        assert ann1.iscovering(ann11)
        assert ann1.iscovering(ann10)
        assert ann1.iscovering(ann12)
        assert ann1.isoverlapping(ann3)
        assert ann1.isoverlapping(ann7)
        assert ann1.isoverlapping(ann10)
        assert ann1.isoverlapping(ann12)
        assert ann1.isoverlapping(ann4)

        assert not ann2.isbefore(ann1)
        assert ann2.isbefore(ann3)
        assert ann2.isleftoverlapping(ann1)
        assert ann2.isoverlapping(ann1)
        assert ann2.isoverlapping(ann10)
        assert not ann2.isoverlapping(ann5)
        assert not ann2.isbefore(ann10)
        assert ann2.gap(ann3) == 12

        assert ann3.iscoextensive(ann9)
        assert ann3.iswithin(ann1)
        assert ann3.isafter(ann2)
        assert ann3.isafter(ann5)
        assert ann3.isafter(ann5, immediately=True)
        assert ann3.isstartingat(ann9)
        assert ann3.isstartingat(ann7)
        assert ann3.isstartingat(ann11)
        assert ann3.isendingwith(ann9)
        assert ann3.isendingwith(ann8)
        assert ann3.gap(ann2) == 12

        assert ann4.isafter(ann3)
        assert not ann4.isafter(ann1)
        assert ann4.isrightoverlapping(ann1)
        assert ann4.isrightoverlapping(ann12)

        assert ann5.isbefore(ann3)
        assert ann5.isbefore(ann3, immediately=True)
        assert ann5.iswithin(ann1)
        assert ann5.isafter(ann2)
        assert not ann5.isafter(ann1)

        assert ann6.isafter(ann3)
        assert ann6.isafter(ann3, immediately=True)

        assert ann7.iscovering(ann7.start)
        assert ann7.isafter(ann5)
        assert ann7.isbefore(ann3)
        assert ann7.isbefore(ann11)
        assert ann7.isafter(ann11)
        assert ann7.isstartingat(ann11)
        assert ann7.isendingwith(ann11)
        assert ann7.isoverlapping(ann7)
        assert ann7.isoverlapping(ann11)
        assert ann7.iswithin(ann9)
        assert ann7.iswithin(ann11)
        assert ann7.isleftoverlapping(ann11)
        assert ann7.isrightoverlapping(ann11)
        assert ann7.iscovering(ann11)
        assert ann11.iscovering(ann7)
        assert ann11.isleftoverlapping(ann7)
        assert ann11.isrightoverlapping(ann7)

        assert ann11.isstartingat(ann7)
        assert ann11.isafter(ann5)
        assert ann11.isbefore(ann3)
        assert ann11.isbefore(ann9)

        # TODO: gaps

    def test_annotation_exps(self):
        import pytest
        with pytest.raises(Exception) as ex:
            Annotation(3, 2, "X")
        assert str(ex.value).startswith("Cannot create annotation")
        with pytest.raises(Exception) as ex:
            Annotation(1, 2, "X", annid="x")
        with pytest.raises(Exception) as ex:
            Annotation(1, 2, "X", features=12)
        with pytest.raises(Exception) as ex:
            Annotation(1, 2, "X", annid="x")
        assert Annotation(2, 3, "X").span == Span(2, 3)
        assert not (Annotation(1, 2, "X") == "X")
        ann1 = Annotation(1, 2, "X")
        assert ann1 == ann1
        assert hash(ann1) == hash((ann1.id, ann1._owner_set))
        with pytest.raises(Exception) as ex:
            Annotation(1, 2, "X") < 33
        assert Annotation(1, 2, "X") < Annotation(2, 3, "X")
        assert not Annotation(1, 2, "X") < Annotation(0, 3, "X")
        assert Annotation(1, 2, "X", annid=0) < Annotation(1, 2, "X", annid=1)
        assert Annotation(1, 2, "X").length == 1

    def test_annotation_misc01(self):
        ann1 = Annotation(1, 2, "x", dict(a=1), annid=3)
        dict1 = ann1.to_dict()
        ann2 = Annotation.from_dict(dict1)
        assert ann1 == ann2

        assert ann2.features == {"a": 1}

        assert str(ann2) == "Annotation(1,2,x,features=Features({'a': 1}),id=3)"
