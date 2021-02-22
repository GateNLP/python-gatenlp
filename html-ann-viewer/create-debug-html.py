from nltk import word_tokenize
from gatenlp import Document
txt = "This is a document   "
#      0123456789012345678901
#      0000000000111111111122
doc = Document("This is a document   ")

annset = doc.annset()
annset.add(0,4,"Token")
annset.add(4,5,"SpaceToken")
annset.add(5,7,"Token")
annset.add(7,8,"SpaceToken")
annset.add(8,9,"Token")
annset.add(9,10,"SpaceToken")
annset.add(10,18,"Token")
annset.add(18,21,"SpaceToken")
annset.add(0,21,"Document")
annset.add(0,18,"Sentence")
annset.add(2,3,"Ann1")
annset.add(2,2,"Zero1")
annset.add(20,20,"Zero2")


doc.save("debug-html.html", fmt="html-ann-viewer", offline=True)
