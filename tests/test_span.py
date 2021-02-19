import sys
from gatenlp import Span


class TestSpanRels:

    def test_span_rels01(self):
        span1 = Span(3, 42)
        span2 = Span(0, 6)
        span3 = Span(18, 24)
        span4 = Span(39, 45)
        span5 = Span(12, 18)
        span6 = Span(24, 30)
        span7 = Span(18, 18)
        span8 = Span(24, 24)
        span9 = Span(18, 24)
        span10 = Span(3, 9)
        span11 = Span(18, 18)
        span12 = Span(36, 42)

        assert span1.iscovering(span1)
        assert span1.iscovering(span1.start)
        assert span1.iscovering(span1.end-1)

        assert span1.isoverlapping(span2)
        assert span1.isrightoverlapping(span1)
        assert span1.iscovering(span3)
        assert not span1.iscovering(span2)
        assert span1.isendingwith(span12)
        assert not span1.isafter(span2)
        assert span1.isstartingat(span10)
        assert span1.iscovering(span5)
        assert span1.iscovering(span7)
        assert span1.iscovering(span11)
        assert span1.iscovering(span10)
        assert span1.iscovering(span12)
        assert span1.isoverlapping(span3)
        assert span1.isoverlapping(span7)
        assert span1.isoverlapping(span10)
        assert span1.isoverlapping(span12)
        assert span1.isoverlapping(span4)

        assert not span2.isbefore(span1)
        assert span2.isbefore(span3)
        assert span2.isleftoverlapping(span1)
        assert span2.isoverlapping(span1)
        assert span2.isoverlapping(span10)
        assert not span2.isoverlapping(span5)
        assert not span2.isbefore(span10)

        assert span3.iscoextensive(span9)
        assert span3.iswithin(span1)
        assert span3.isafter(span2)
        assert span3.isafter(span5)
        assert span3.isafter(span5, immediately=True)
        assert span3.isstartingat(span9)
        assert span3.isstartingat(span7)
        assert span3.isstartingat(span11)
        assert span3.isendingwith(span9)
        assert span3.isendingwith(span8)

        assert span4.isafter(span3)
        assert not span4.isafter(span1)
        assert span4.isrightoverlapping(span1)
        assert span4.isrightoverlapping(span12)

        assert span5.isbefore(span3)
        assert span5.isbefore(span3, immediately=True)
        assert span5.iswithin(span1)
        assert span5.isafter(span2)
        assert not span5.isafter(span1)

        assert span6.isafter(span3)
        assert span6.isafter(span3, immediately=True)

        assert span7.iscovering(span7.start)
        assert span7.isafter(span5)
        assert span7.isbefore(span3)
        assert span7.isbefore(span11)
        assert span7.isafter(span11)
        assert span7.isstartingat(span11)
        assert span7.isendingwith(span11)
        assert span7.isoverlapping(span7)
        assert span7.isoverlapping(span11)
        assert span7.iswithin(span9)
        assert span7.iswithin(span11)
        assert span7.isleftoverlapping(span11)
        assert span7.isrightoverlapping(span11)
        assert span7.iscovering(span11)
        assert span11.iscovering(span7)
        assert span11.isleftoverlapping(span7)
        assert span11.isrightoverlapping(span7)

        assert span11.isstartingat(span7)
        assert span11.isafter(span5)
        assert span11.isbefore(span3)
        assert span11.isbefore(span9)

    def test_span_basic01(self):

        assert Span(0, 3) == Span(0, 3)
        assert not Span(0, 3) == Span(0, 4)
        assert not Span(0, 3) == 1
        assert not Span(5, 8) < Span(0, 4)
        assert Span(0, 3) < Span(1, 4)
        span1 = Span(0, 3)
        span2 = Span(7, 9)
        assert span1 == span1
        assert str(span1) == "Span(0,3)"
        assert span1.length == 3
        assert span1.gap(span2) == 4
        assert span2.gap(span1) == 4

    def test_span_excp01(self):
        import pytest
        with pytest.raises(Exception) as ex:
            Span(3, 2) < 2

class TestSpanEmbed:

    def testSpanEmbed01(self):

        ret = Span.squeeze(0, 7, 7)
        assert ret == [Span(0,1), Span(1,2), Span(2,3), Span(3,4), Span(4,5), Span(5,6), Span(6,7)]
        ret = Span.squeeze(0, 7, 2)
        assert ret == [Span(0,4), Span(4,7)]
        ret = Span.squeeze(0, 3, 2)
        assert ret == [Span(0, 2), Span(2, 3)]
        ret = Span.squeeze(0, 1, 2)
        assert ret == [Span(0, 1), Span(0, 1)]
        ret = Span.squeeze(0, 3, 5)
        assert ret == [Span(0, 1), Span(1, 2), Span(2, 3), Span(2, 3), Span(2, 3)]
        ret = Span.squeeze(0, 7, 3)
        assert ret == [Span(0, 3), Span(3, 5), Span(5, 7)]
        ret = Span.squeeze(0, 7, 6)
        assert ret == [Span(0,2), Span(2,3), Span(3,4), Span(4,5), Span(5,6), Span(6,7)]
