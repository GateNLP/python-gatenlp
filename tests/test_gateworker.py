"""
Module to test the GateWorker and GateWorkerAnnotator
"""
import os

from gatenlp import Document
from gatenlp.utils import init_logger
from gatenlp.gateworker import GateWorker

logger = init_logger("test_gateworker")

should_exit = not os.environ.get("GATE_HOME")
if should_exit:
    logger.warning("Environment variable GATE_HOME not set, skipping tests in TestGateWorker")


def make_doc1():
    """
    Create and return a document for testing
    """
    doc = Document("This is just some test document. It mentions New York.")
    return doc


class TestGateWorker:

    def test_gateworker01(self):
        """
        Unit test method (make linter happy)
        """
        if should_exit:
            return
        txt = "some text"
        with GateWorker() as gw1:
            gdoc1 = gw1.createDocument(txt)
            pdoc1 = gw1.gdoc2pdoc(gdoc1)
            assert pdoc1.text == txt

