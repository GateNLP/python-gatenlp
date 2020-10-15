# Getting Started and Usage Examples

## Basic Operations

Create a new document within Python from a given string, set a document feature
and add an annotation that spans the whole document to the default
annotation set:


```python
from gatenlp import Document

# Create the document
doc1 = Document("This is the text of the document.")

# set a document feature
doc1.features["purpose"] = "simple illustration of gatenlp basics"

# get the default annotation set
defset = doc1.annset()

# add an annotation that spans the whole document, no features
defset.add(0, len(doc1), "Document", {})
```




    Annotation(0,33,Document,features=Features({}),id=0)



Now save the document in bdocjson format and load back from the saved
document:


```python
# save the document in bdocjson format, this can be read into Java GATE
# using the format-bdoc plugin.
doc1.save("testdoc.bdocjs")
# Read back the document
doc2 = Document.load("testdoc.bdocjs")


# print the json representation of the loaded document
print(doc2.save_mem(fmt="json"))
```

    {"annotation_sets": {"": {"name": "", "annotations": [{"type": "Document", "start": 0, "end": 33, "id": 0, "features": {}}], "next_annid": 1}}, "text": "This is the text of the document.", "features": {"purpose": "simple illustration of gatenlp basics"}, "offset_type": "p", "name": ""}


Tokenize and create annotations for the tokens using a NLTK tokenizer:



```python
from gatenlp.processing.tokenizer import NLTKTokenizer
from nltk.tokenize import TreebankWordTokenizer

nltk_tok = TreebankWordTokenizer()
ann_tok = NLTKTokenizer(nltk_tokenizer=nltk_tok, out_set="NLTK")
doc1 = ann_tok(doc1)
```

Get all the annotation for the NLTK tokens which are in annotation set "NLTK":



```python
# get the annotation set with the name "NLTK" and print the number of annotations
set_nltk = doc1.annset("NLTK")
print(len(set_nltk))

# get only annotations of annotation type "Token" from the set and print the number of annotations
# since there are no other annotations in the original set, the number should be the same
set_tokens = set_nltk.with_type("Token")
print(len(set_tokens))

# print all the annotations in order
for ann in set_tokens:
    print(ann)

```

    8
    8
    Annotation(0,4,Token,features=Features({}),id=0)
    Annotation(5,7,Token,features=Features({}),id=1)
    Annotation(8,11,Token,features=Features({}),id=2)
    Annotation(12,16,Token,features=Features({}),id=3)
    Annotation(17,19,Token,features=Features({}),id=4)
    Annotation(20,23,Token,features=Features({}),id=5)
    Annotation(24,32,Token,features=Features({}),id=6)
    Annotation(32,33,Token,features=Features({}),id=7)


The annotation set `set_nltk` is an original annotation set and reflects directly what is stored with the 
document: it is an "attached" annotation set. Adding or removing annotations in that set will change what is stored with the document. 

On the other hand, the annotation set `set_tokens` is the result of a filtering operation and is "detached". 
By default it is immutable, it cannot be modified. It can be made mutable, but when annotations are then added or removed from the set, this will not change what is stored with the document. 


```python
# check if the set_nltk is detached
print("set_nltk is detached: ", set_nltk.isdetached())  # no it is attached! 
print("set_nltk is immutable: ", set_nltk.immutable )  # no
# add an annotation to the set
set_nltk.add(3,5,"New1")

# check if the set_tokens is detached
print("set_tokens is detached: ", set_tokens.isdetached())  # yes!
# check if it is immutable as well
print("set_tokens is immutable: ", set_tokens.immutable )  # yes
try:
    set_tokens.add(5,7,"New2")
except Exception as ex:
    print("Error:", ex)
    
# ok, let's make the set mutable and add the annotation
set_tokens.immutable = False
set_tokens.add(5,7,"New2")

print("set_nltk: size=", len(set_nltk), ", annotation:", set_nltk)
print("set_tokens: size=", len(set_tokens), ", annotations: ",   set_tokens)
```

    set_nltk is detached:  False
    set_nltk is immutable:  False
    set_tokens is detached:  True
    set_tokens is immutable:  True
    Error: Cannot add an annotation to an immutable annotation set
    set_nltk: size= 9 , annotation: AnnotationSet([Annotation(0,4,Token,features=Features({}),id=0), Annotation(3,5,New1,features=Features({}),id=8), Annotation(5,7,Token,features=Features({}),id=1), Annotation(8,11,Token,features=Features({}),id=2), Annotation(12,16,Token,features=Features({}),id=3), Annotation(17,19,Token,features=Features({}),id=4), Annotation(20,23,Token,features=Features({}),id=5), Annotation(24,32,Token,features=Features({}),id=6), Annotation(32,33,Token,features=Features({}),id=7)])
    set_tokens: size= 9 , annotations:  AnnotationSet([Annotation(0,4,Token,features=Features({}),id=0), Annotation(5,7,Token,features=Features({}),id=1), Annotation(5,7,New2,features=Features({}),id=8), Annotation(8,11,Token,features=Features({}),id=2), Annotation(12,16,Token,features=Features({}),id=3), Annotation(17,19,Token,features=Features({}),id=4), Annotation(20,23,Token,features=Features({}),id=5), Annotation(24,32,Token,features=Features({}),id=6), Annotation(32,33,Token,features=Features({}),id=7)])


Adding the annotation with type "New1" to `set_nltk` actually stored the annotation with the document, but did not affect the filtered set `set_tokens`, and adding the annotation with type "New2" to the filtered set did not affect the set stored with the document. 

The document and document features and the annotation sets and annotation as well as their features can be shown in a Jupyter notebook by simply showing a document value:


```python
doc1
```




<div><style>#GDPFPTPQAZ-wrapper { color: black !important; }</style>
<div id="GDPFPTPQAZ-wrapper">

<div>
<style>
#GDPFPTPQAZ-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.GDPFPTPQAZ-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.GDPFPTPQAZ-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.GDPFPTPQAZ-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.GDPFPTPQAZ-label {
    margin-bottom: -15px;
    display: block;
}

.GDPFPTPQAZ-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#GDPFPTPQAZ-popup {
    display: none;
    color: black;
    position: absolute;
    margin-top: 10%;
    margin-left: 10%;
    background: #aaaaaa;
    width: 60%;
    height: 60%;
    z-index: 50;
    padding: 25px 25px 25px;
    border: 1px solid black;
    overflow: auto;
}

.GDPFPTPQAZ-selection {
    margin-bottom: 5px;
}

.GDPFPTPQAZ-featuretable {
    margin-top: 10px;
}

.GDPFPTPQAZ-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.GDPFPTPQAZ-fvalue {
    text-align: left !important;
}
</style>
  <div id="GDPFPTPQAZ-content">
        <div id="GDPFPTPQAZ-popup" style="display: none;">
        </div>
        <div class="GDPFPTPQAZ-row" id="GDPFPTPQAZ-row1" style="height:67vh; min-height:100px;">
            <div id="GDPFPTPQAZ-text-wrapper" class="GDPFPTPQAZ-col" style="width:70%;">
                <div class="GDPFPTPQAZ-hdr" id="GDPFPTPQAZ-dochdr"></div>
                <div id="GDPFPTPQAZ-text">
                </div>
            </div>
            <div id="GDPFPTPQAZ-chooser" class="GDPFPTPQAZ-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="GDPFPTPQAZ-row" id="GDPFPTPQAZ-row2" style="height:30vh; min-height: 100px;">
            <div id="GDPFPTPQAZ-details" class="GDPFPTPQAZ-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.10/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="GDPFPTPQAZ-data">
    {"annotation_sets": {"": {"name": "detached-from:", "annotations": [{"type": "Document", "start": 0, "end": 33, "id": 0, "features": {}}], "next_annid": 1}, "NLTK": {"name": "detached-from:NLTK", "annotations": [{"type": "Token", "start": 0, "end": 4, "id": 0, "features": {}}, {"type": "Token", "start": 5, "end": 7, "id": 1, "features": {}}, {"type": "Token", "start": 8, "end": 11, "id": 2, "features": {}}, {"type": "Token", "start": 12, "end": 16, "id": 3, "features": {}}, {"type": "Token", "start": 17, "end": 19, "id": 4, "features": {}}, {"type": "Token", "start": 20, "end": 23, "id": 5, "features": {}}, {"type": "Token", "start": 24, "end": 32, "id": 6, "features": {}}, {"type": "Token", "start": 32, "end": 33, "id": 7, "features": {}}, {"type": "New1", "start": 3, "end": 5, "id": 8, "features": {}}], "next_annid": 9}}, "text": "This is the text of the document.", "features": {"purpose": "simple illustration of gatenlp basics"}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("GDPFPTPQAZ-");
    </script>
  </div>

</div></div>




```python

```
