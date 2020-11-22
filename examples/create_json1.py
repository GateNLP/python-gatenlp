from gatenlp.document import Document
from gatenlp.docformats import simplejson
from gatenlp.offsetmapper import OFFSET_TYPE_JAVA

doc1 = Document("Just a simple \U0001F4A9 document.")
annset1 = doc1.annset("")
ann1 = annset1.add(0, 4, "Token", {"n": 1, "upper": True})
ann2 = annset1.add(5, 6, "Token", {"n": 2, "upper": False})
ann3 = annset1.add(7, 13, "Token", {"n": 3, "upper": False})
ann4 = annset1.add(14, 15, "Token", {"n": 4, "upper": False, "isshit": True})
ann5 = annset1.add(16, 24, "Token", {"n": 5})
annset2 = doc1.annset("Set2")
annset2.add(0, 12, "Ann1", None)
annset1.remove(ann2.id)
annset1.get(ann3.id).set_feature("str", "simple")
doc1.set_feature("docfeature1", "value1")
doc1.set_feature("docfeature1", "value1b")
simplejson.dump_file(doc1, "doc1.bdocjson")
simplejson.dump_file(doc1, "doc1.bdocjson.gz")
