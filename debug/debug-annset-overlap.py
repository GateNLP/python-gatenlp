from gatenlp import Document, Span

doc = Document("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
set1 = doc.annset("set1")
set2 = doc.annset("set2")
ann1 = set1.add(13, 17, "sometype")
ann2 = set2.add(16, 17, "sometype")
ret = set1.overlapping(ann2, include_self=True)
print(ret)
