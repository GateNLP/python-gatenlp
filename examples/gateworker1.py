#!/usr/bin/env python

from gatenlp.gateworker import GateWprler

gs = GateWorker()

doc1 = gs.worker.loadDocumentFromFile("testdoc.bdocjson", "text/bdocjs")

print("GATE Document:", doc1)

gs.worker.print2err("SOME MESSAGE TO ERR!!\n")
gs.worker.print2out("SOME MESSAGE TO OUT!!\n")

pdoc = gs.gdoc2pdoc(doc1)

print("Python Document:", pdoc)

gs.worker.loadMavenPlugin("uk.ac.gate.plugins", "annie", "8.6")
pipeline = gs.worker.loadPipelineFromPlugin(
    "uk.ac.gate.plugins", "annie", "/resources/ANNIE_with_defaults.gapp"
)

gs.worker.run4Document(pipeline, doc1)

pdoc = gs.gdoc2pdoc(doc1)

print("Python Document after ANNIE:", pdoc)

gs.worker.saveDocumentToFile(doc1, "saveddoc.xml", "")


gs.close()
