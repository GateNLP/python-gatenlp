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

doc = Document("   x   y   ")
doc.annset().add(0,1,"Space")
doc.annset().add(1,2,"Space")
doc.annset().add(2,3,"Space")
doc.annset().add(3,4,"Token")
doc.annset().add(4,5,"Space")
doc.annset().add(5,6,"Space")
doc.annset().add(6,7,"Space")
doc.annset().add(7,8,"Token")
doc.annset().add(8,10,"Space")
doc.annset().add(10,11,"Space")
doc.save("debug-html2.html", fmt="html-ann-viewer", offline=True)
