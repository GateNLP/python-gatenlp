#!/usr/bin/env python

from gatenlp.gateslave import GateSlave

gs = GateSlave()

doc1 = gs.slave.loadDocumentFromFile("testdoc.bdocjson", "text/bdocjs")

print("GATE Document:", doc1)

gs.slave.print2err("SOME MESSAGE TO ERR!!\n")
gs.slave.print2out("SOME MESSAGE TO OUT!!\n")

pdoc = gs.gdoc2pdoc(doc1)

print("Python Document:", pdoc)

gs.slave.loadMavenPlugin("uk.ac.gate.plugins", "annie", "8.6")
pipeline = gs.slave.loadPipelineFromPlugin(
    "uk.ac.gate.plugins", "annie", "/resources/ANNIE_with_defaults.gapp"
)

gs.slave.run4Document(pipeline, doc1)

pdoc = gs.gdoc2pdoc(doc1)

print("Python Document after ANNIE:", pdoc)

gs.slave.saveDocumentToFile(doc1, "saveddoc.xml", "")


gs.close()
