#!/usr/bin/env python

from gatenlp.gateslave import GateSlave

gs = GateSlave(use_auth_token=True, port=25333, start=False, auth_token="geheim")
# gs = GateSlave(use_auth_token=True, port=25335, auth_token="c281f5a8-977d-4bc6-9018-d62e39af4d53", start=True)

# gs.slave.logActions(True)

doc1 = gs.slave.createDocument(
    "This is a 💩 document. It mentions Barack Obama and George Bush and New York."
)
print("GATE Document:", doc1)

pdoc = gs.gdoc2pdoc(doc1)
print("Python gatenlp document:", pdoc)

gs.slave.loadMavenPlugin("uk.ac.gate.plugins", "annie", "8.6")
pipeline = gs.slave.loadPipelineFromPlugin(
    "uk.ac.gate.plugins", "annie", "/resources/ANNIE_with_defaults.gapp"
)

gs.slave.run4Document(pipeline, doc1)
print("GATE Document after ANNIE:", doc1)

pdoc = gs.gdoc2pdoc(doc1)
print("Python gatenlp document after ANNIE:", pdoc)

anns = pdoc.annset()

tokens = anns.with_type("Token")
print(f"Got {len(tokens)} tokens")

persons = anns.with_type("Person")
print(f"Got {len(persons)} Person annotations:")
for ann in persons:
    print(f"- {pdoc[ann]} from {ann.start} to {ann.end}")

gs.slave.saveDocumentToFile(doc1, "tmp_saveddoc.xml", "")

pdoc.save("tmp_saveddoc.bdocjs")

# gs.slave.kill()

gs.close()
