# Examples of using the gatenlp package

## Basic Operations

Create a new document within Python from a given string, set a document feature
and add an annotation that spans the whole document to the default
annotation set:

```python
from gatenlp import Document

# Create the document
doc1 = Document("This is the text of the document.")
# set a document feature
doc1.set_feature("purpose", "simple illustration of gatenlp basics")
# get the default annotation set
defset = doc1.get_annotations()
# add an annotation that spans the whole document, no features
defset.add(0, len(doc1), "Document", {})
```

Now save the document in bdocjson format and load back from the saved
document:

```python
from gatenlp.docformats import simplejson

# save the document in bdocjson format, this can be read into Java GATE
# using the format-bdoc plugin.
simepljson.dump_file(doc1, "testdoc.bdocjson")
# Read back the document
doc2 = simplejson.load_file("testdoc.bdocjson")
# print the json representation of the loaded document
print(simplejson.dumps(doc2))
```

Tokenize and create annotations for the tokens:

```python
pat = r'''(?x)(?:[A-Z]\.)+|\d+:\d|(?:https?://)?(?:\w+\.)(?:\w{2,})+(?:[\w/]+)|[@\#]?\w+(?:[-']\w+)*|\$\d+(?:\.\d+)?%?|\.\.\.|[!?]+'''
defset = doc1.get_annotations()
for m in re.finditer(pat, doc1.text):
  defset.add(m.start(), m.end(), "Token", {})
```
