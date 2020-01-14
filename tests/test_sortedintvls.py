import logging
from gatenlp.impl import SortedIntvls
logging.basicConfig()
logger = logging.getLogger("gatenlp")
logger.setLevel(logging.INFO)

# Simple simulation of the interaction: instead of calling interact() manually call
# the methods from the created wrapper.
class TestSortedIntvls01:
    def test_sortedintvls01(self):
        si1 = SortedIntvls()
        intvls = [
            (0, 3, "int1"),
            (4, 5, "int2"),
            (9, 10, "int9"),
            (5, 9, "int6"),
            (4, 10, "int4"),
            (8, 10, "int8"),
            (5, 6, "int5"),
            (0, 20, "int0"),
            (8, 9, "int7"),
            (4, 5, "int3"),
        ]
        si1.update(intvls)
        logger.info("!! si1 is {}".format(si1))
        ret1 = list(si1.firsts())
        logger.info("firsts={}".format(ret1))
        assert len(ret1) == 2
        assert (0, 3, "int1") in ret1
        assert (0, 20, "int0") in ret1
        ret2 = list(si1.lasts())
        logger.info("lasts={}".format(ret2))
        assert len(ret2) == 1
        assert (9, 10, "int9") in ret2
        ret3 = list(si1.starting_at(4))
        logger.info("starting at 4={}".format(ret3))
        assert len(ret3) == 3
        assert (4, 5, "int2") in ret3
        assert (4, 10, "int4") in ret3
        assert (4, 5, "int3") in ret3
        ret4 = list(si1.within(3, 8))
        logger.info("contained in 3,8={}".format(ret4))
        assert len(ret4) == 3
        assert (4, 5, "int2") in ret4
        assert (4, 5, "int3") in ret4
        assert (5, 6, "int5") in ret4
        ret5 = list(si1.within(0, 20))
        logger.info("contained in 0,20={}".format(ret5))
        assert len(ret5) == len(intvls)
        ret6 = list(si1.covering(3, 4))
        logger.info("containing 3,4={}".format(ret6))
        assert len(ret6) == 1
        assert (0, 20, "int0") in ret6
        ret7 = list(si1.covering(8, 9))
        logger.info("containing 8,9={}".format(ret7))
        assert len(ret7) == 5
        assert (0, 20, 'int0') in ret7
        assert (4, 10, 'int4') in ret7
        assert (5, 9, 'int6') in ret7
        assert (8, 10, 'int8') in ret7
        assert (8, 9, 'int7') in ret7