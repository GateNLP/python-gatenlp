from gatenlp.docformats import simplejson
import gatenlp
from gatenlp.document import Document

with open("test-doc1.gate_sj", "rt", encoding="utf-8") as fp:
    doc = simplejson.load(fp)
# bdoc=gatenlp.document.Document.from_json_map(doc)
set1 = doc.annset()
print("Covering 0,1: ", set1.covering(0, 1))
