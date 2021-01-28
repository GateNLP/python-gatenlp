import sys
from gatenlp import Document

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
        ann1 = set1.with_type("Ann1").by_idx(0)
        ann2 = set1.with_type("Ann2").by_idx(0)
        ann3 = set1.with_type("Ann3").by_idx(0)
        ann4 = set1.with_type("Ann4").by_idx(0)
        ann5 = set1.with_type("Ann5").by_idx(0)
        ann6 = set1.with_type("Ann6").by_idx(0)
        ann7 = set1.with_type("Ann7").by_idx(0)
        ann8 = set1.with_type("Ann8").by_idx(0)
        ann9 = set1.with_type("Ann9").by_idx(0)
        ann10 = set1.with_type("Ann10").by_idx(0)
        ann11 = set1.with_type("Ann11").by_idx(0)
        ann12 = set1.with_type("Ann12").by_idx(0)

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

        assert ann3.iscoextensive(ann9)
        assert ann3.iswithin(ann1)
        assert ann3.isafter(ann2)
        assert ann3.isafter(ann5)
        assert ann3.isafter(ann5, immediately=True)

        assert ann5.isbefore(ann3)
        assert ann5.isbefore(ann3, immediately=True)


