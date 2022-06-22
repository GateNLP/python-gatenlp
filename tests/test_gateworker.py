"""
Module to test the GateWorker and GateWorkerAnnotator
"""
import os
import py4j
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

WORKER_ATTRS = [
    "createDocument", "deleteResource", "findMavenPlugin", "gate_build",
    "gate_version", "getBdocJson", "getClass", "getCorpus4Name", "getCorpusNames",
    "getDocument4BdocJson", "getDocument4Name", "getDocumentNames", "getPipeline4Name",
    "getPipelineNames", "getPr4Name", "getPrNames", "getResources4Name",
    "jsonAnnsets4Doc", "loadDocumentFromFile", "loadMavenPlugin", "loadPipelineFromFile",
    "loadPipelineFromPlugin", "loadPipelineFromUri", "logActions", "newCorpus",
    "pluginBuild", "pluginVersion", "print2err", "print2out", "run4Corpus", "run4Document",
    "runExecutionFinished", "runExecutionStarted", "saveDocumentToFile", "showGui",
    "toString"
]

class TestGateWorker:

    def test_gateworker01(self):
        """
        Unit test method (make linter happy)
        """
        if should_exit:
            return
        txt = "some text"
        with GateWorker(port=33117) as gw1:
            assert gw1.jvm is not None
            assert hasattr(gw1.jvm, "gate")
            assert hasattr(gw1.jvm.gate, "Factory")
            assert gw1.worker is not None
            assert gw1.gate_version is not None
            assert isinstance(gw1.gate_version, str)
            assert gw1.gate_build is not None and isinstance(gw1.gate_build, str)
            assert gw1.worker_version is not None and isinstance(gw1.worker_version, str)
            assert gw1.worker_build is not None and isinstance(gw1.worker_build, str)
            assert gw1.gatehome is not None and isinstance(gw1.gatehome, str)
            assert gw1.port is not None and isinstance(gw1.port, int)
            assert gw1.host is not None and isinstance(gw1.host, str)
            assert gw1.gateprocess is not None and isinstance(gw1.gateprocess.pid, int)
            assert isinstance(gw1.getpid, int)

            gdoc1 = gw1.createDocument(txt)
            pdoc1 = gw1.gdoc2pdoc(gdoc1)
            assert pdoc1.text == txt

            gdoc2 = gw1.load_gdoc(os.path.join("docs", "testdocument1.xml"))
            assert gdoc2.getAnnotations().size() == 14
            pdoc2 = gw1.gdoc2pdoc(gdoc2)
            assert len(pdoc2.annset()) == 14
            toks = pdoc2.annset().with_type("Token")
            assert len(toks) == 6

            gdoc2a = gw1.pdoc2gdoc(pdoc2)
            assert gdoc2a.getAnnotations().size() == 14
            gdoc2a = gw1.pdoc2gdoc(pdoc2, annspec=[("", "Token")])
            assert gdoc2a.getAnnotations().size() == 6

            pdoc3a = Document(text=pdoc2.text)
            pdoc3a = gw1.gdocanns2pdoc(gdoc2, pdoc3a)
            assert len(pdoc3a.annset()) == 14
            pdoc3b = Document(text=pdoc2.text)
            pdoc3b = gw1.gdocanns2pdoc(gdoc2, pdoc3b, annspec=[("", "Token")])
            assert len(pdoc3b.annset()) == 6

            gdoc4 = gw1.createDocument("Some Text")
            assert gdoc4.getStringContent() == "Some Text"


