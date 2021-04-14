"""
Module to test the GateWorker and GateWorkerAnnotator
"""
import os
import sys

from gatenlp import Document


def make_doc1():
    """
    Create and return a document for testing
    """
    doc = Document("This is just some test document. It mentions New York.")
    return doc


def should_exit():
    if not os.environ.get("GATE_HOME"):
        print("Environment variable GATE_HOME not set, skipping TestGateWorker",
              file=sys.stderr)
        return True
    return False


class TestGateWorker:

    def test_gateworker01(self):
        """
        Unit test method (make linter happy)
        """
        if should_exit():
            return
        print("Environment variable GATE_HOME set, running TestGateWorker",
              file=sys.stderr)
