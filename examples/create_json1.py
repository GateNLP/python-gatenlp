from gatenlp.document import Document
from gatenlp.docformats import simplejson
from gatenlp.offsetmapper import OFFSET_TYPE_JAVA

doc1 = Document("Just a simple \U0001F4A9 document.")
annset1 = doc1.get_annotations("")
ann1id = annset1.add(0, 4, "Token", {"n": 1, "upper": True})
ann2id = annset1.add(5, 6, "Token", {"n": 2, "upper": False})
ann3id = annset1.add(7, 13, "Token", {"n": 3, "upper": False})
ann4id = annset1.add(14, 15, "Token", {"n": 4, "upper": False, "isshit": True})
ann5id = annset1.add(16, 24, "Token", {"n": 5})
annset2 = doc1.get_annotations("Set2")
annset2.add(0, 12, "Ann1", None)
annset1.remove(ann2id)
annset1.get(ann3id).set_feature("str", "simple")
doc1.set_feature("docfeature1", "value1")
doc1.set_feature("docfeature1", "value1b")
simplejson.dump_file(doc1, "doc1.bdocjson")
simplejson.dump_file(doc1, "doc1.bdocjson.gz")

