# Documents


```python
from gatenlp import Document

```


```python
# To load a document from a file with the name "file.bdocjs" into gatenlp simply use:
# doc = Document.load("test2a.bdocjs")

# But it is also possible to load from a file that is somewhere on the internet. For this notebook, we use
# an example document that gets loaded from a URL:
doc = Document.load("https://gatenlp.github.io/python-gatenlp/testdocument1.txt")

# We can visualize the document by printing it:
print(doc)
```

    Document(This is a test document.
    
    It contains just a few sentences. 
    Here is a sentence that mentions a few named entities like 
    the persons Barack Obama or Ursula von der Leyen, locations
    like New York City, Vienna or Beijing or companies like 
    Google, UniCredit or Huawei. 
    
    Here we include a URL https://gatenlp.github.io/python-gatenlp/ 
    and a fake email address john.doe@hiscoolserver.com as well 
    as #some #cool #hastags and a bunch of emojis like 😽 (a kissing cat),
    👩‍🏫 (a woman teacher), 🧬 (DNA), 
    🧗 (a person climbing), 
    💩 (a pile of poo). 
    
    Here we test a few different scripts, e.g. Hangul 한글 or 
    simplified Hanzi 汉字 or Farsi فارسی which goes from right to left. 
    
    
    ,features=Features({}),anns=[])


Printing the document shows the document text and indicates that there are no document features and no 
annotations which is to be expected since we just loaded from a plain text file. 

In a Jupyter notebook, a `gatenlp` document can also be visualized graphically by either just using the document 
as the last value of a cell or by using the IPython "display" function:


```python
from IPython.display import display
display(doc)
```



            <style>
              div#GOLHJFIHAP-wrapper: { color: black: !important; }
            </style>
            <div id="GOLHJFIHAP-wrapper">

<div>
<style>
#GOLHJFIHAP-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.GOLHJFIHAP-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.GOLHJFIHAP-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.GOLHJFIHAP-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.GOLHJFIHAP-label {
    margin-bottom: -15px;
    display: block;
}

.GOLHJFIHAP-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#GOLHJFIHAP-popup {
    display: none;
    colour: white;
    position: absolute;
    margin-top: 10%;
    margin-left: 10%;
    background: #ff88ff;
    width: 60%;
    height: 60%;
    z-index: 50;
    padding: 25px 25px 25px;
    border: 1px solid black;
    overflow: auto;
}

.GOLHJFIHAP-selection {
    margin-bottom: 5px;
}

.GOLHJFIHAP-featuretable {
    margin-top: 10px;
}

.GOLHJFIHAP-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.GOLHJFIHAP-fvalue {
    text-align: left !important;
}
</style>
  <div id="GOLHJFIHAP-content">
        <div id="GOLHJFIHAP-popup" style="display: none;">
        </div>
        <div class="GOLHJFIHAP-row" id="GOLHJFIHAP-row1" style="height:67vh; min-height:100px;">
            <div id="GOLHJFIHAP-text-wrapper" class="GOLHJFIHAP-col" style="width:70%;">
                <div class="GOLHJFIHAP-hdr" id="GOLHJFIHAP-dochdr"></div>
                <div id="GOLHJFIHAP-text">
                </div>
            </div>
            <div id="GOLHJFIHAP-chooser" class="GOLHJFIHAP-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="GOLHJFIHAP-row" id="GOLHJFIHAP-row2" style="height:30vh; min-height: 100px;">
            <div id="GOLHJFIHAP-details" class="GOLHJFIHAP-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.8/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="GOLHJFIHAP-data">
    {"annotation_sets": {}, "text": "This is a test document.\n\nIt contains just a few sentences. \nHere is a sentence that mentions a few named entities like \nthe persons Barack Obama or Ursula von der Leyen, locations\nlike New York City, Vienna or Beijing or companies like \nGoogle, UniCredit or Huawei. \n\nHere we include a URL https://gatenlp.github.io/python-gatenlp/ \nand a fake email address john.doe@hiscoolserver.com as well \nas #some #cool #hastags and a bunch of emojis like \ud83d\ude3d (a kissing cat),\n\ud83d\udc69\u200d\ud83c\udfeb (a woman teacher), \ud83e\uddec (DNA), \n\ud83e\uddd7 (a person climbing), \n\ud83d\udca9 (a pile of poo). \n\nHere we test a few different scripts, e.g. Hangul \ud55c\uae00 or \nsimplified Hanzi \u6c49\u5b57 or Farsi \u0641\u0627\u0631\u0633\u06cc which goes from right to left. \n\n\n", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("GOLHJFIHAP-");
    </script>
  </div>

            </div>



This shows the document in a layout that has three areas: the document text in the upper left,
the list of annotation set and type names in the upper right and document or annotation features
at the bottom. In the example above only the text is shown because there are no document features or 
annotations. 

## Document features

Lets add some document features:


```python
doc.features["loaded-from"] = "https://gatenlp.github.io/python-gatenlp/testdocument1.txt"
doc.features["purpose"] = "test document for gatenlp"
doc.features["someotherfeature"] = 22
doc.features["andanother"] = {"what": "a dict", "alist": [1,2,3,4,5]}
```

Document features map feature names to feature values and behave a lot like a Python dictionary. Feature names
should always be strings, feature values can be anything, but a document can only be stored or exchanged with Java GATE if feature values are restricted to whatever can be serialized with JSON: dictionaries, lists, numbers, strings and booleans. 

Now that we have create document features the document is shown like this:


```python
doc
```





            <style>
              div#PWHVVMOVVQ-wrapper: { color: black: !important; }
            </style>
            <div id="PWHVVMOVVQ-wrapper">

<div>
<style>
#PWHVVMOVVQ-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.PWHVVMOVVQ-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.PWHVVMOVVQ-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.PWHVVMOVVQ-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.PWHVVMOVVQ-label {
    margin-bottom: -15px;
    display: block;
}

.PWHVVMOVVQ-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#PWHVVMOVVQ-popup {
    display: none;
    colour: white;
    position: absolute;
    margin-top: 10%;
    margin-left: 10%;
    background: #ff88ff;
    width: 60%;
    height: 60%;
    z-index: 50;
    padding: 25px 25px 25px;
    border: 1px solid black;
    overflow: auto;
}

.PWHVVMOVVQ-selection {
    margin-bottom: 5px;
}

.PWHVVMOVVQ-featuretable {
    margin-top: 10px;
}

.PWHVVMOVVQ-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.PWHVVMOVVQ-fvalue {
    text-align: left !important;
}
</style>
  <div id="PWHVVMOVVQ-content">
        <div id="PWHVVMOVVQ-popup" style="display: none;">
        </div>
        <div class="PWHVVMOVVQ-row" id="PWHVVMOVVQ-row1" style="height:67vh; min-height:100px;">
            <div id="PWHVVMOVVQ-text-wrapper" class="PWHVVMOVVQ-col" style="width:70%;">
                <div class="PWHVVMOVVQ-hdr" id="PWHVVMOVVQ-dochdr"></div>
                <div id="PWHVVMOVVQ-text">
                </div>
            </div>
            <div id="PWHVVMOVVQ-chooser" class="PWHVVMOVVQ-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="PWHVVMOVVQ-row" id="PWHVVMOVVQ-row2" style="height:30vh; min-height: 100px;">
            <div id="PWHVVMOVVQ-details" class="PWHVVMOVVQ-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.8/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="PWHVVMOVVQ-data">
    {"annotation_sets": {}, "text": "This is a test document.\n\nIt contains just a few sentences. \nHere is a sentence that mentions a few named entities like \nthe persons Barack Obama or Ursula von der Leyen, locations\nlike New York City, Vienna or Beijing or companies like \nGoogle, UniCredit or Huawei. \n\nHere we include a URL https://gatenlp.github.io/python-gatenlp/ \nand a fake email address john.doe@hiscoolserver.com as well \nas #some #cool #hastags and a bunch of emojis like \ud83d\ude3d (a kissing cat),\n\ud83d\udc69\u200d\ud83c\udfeb (a woman teacher), \ud83e\uddec (DNA), \n\ud83e\uddd7 (a person climbing), \n\ud83d\udca9 (a pile of poo). \n\nHere we test a few different scripts, e.g. Hangul \ud55c\uae00 or \nsimplified Hanzi \u6c49\u5b57 or Farsi \u0641\u0627\u0631\u0633\u06cc which goes from right to left. \n\n\n", "features": {"loaded-from": "https://gatenlp.github.io/python-gatenlp/testdocument1.txt", "purpose": "test document for gatenlp", "someotherfeature": 22, "andanother": {"what": "a dict", "alist": [1, 2, 3, 4, 5]}}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("PWHVVMOVVQ-");
    </script>
  </div>

            </div>





```python
# to retrieve a feature value we can do:
doc.features["purpose"]
```




    'test document for gatenlp'




```python
# If a feature does not exist, None is returned or a default value if specified:
print(doc.features.get("doesntexist"))
print(doc.features.get("doesntexist", "MV!"))

```

    None
    MV!


## Annotations

Lets add some annotations too. Annotations are items of information for some range of characters within the document. They can be used to represent information about things like tokens, entities, sentences, paragraphs, or 
anything that corresponds to some contiguous range of offsets in the document.

Annotations consist of the following parts:
* The "start" and "end" offset to identify the text the annotation refers to
* A "type" which is an arbitrary name that identifies what kind of thing the annotation describes, e.g. "Token"
* Features: these work in the same way as for the whole document: an arbitrary set of feature name / feature value
  pairs which provide more information, e.g. for a Token the features could include the lemma, the part of speech,
  the stem, the number, etc. 

Annotations can be organized in "annotation sets". Each annotation set has a name and a set of annotations. There can be as many sets as needed. 

Annotation can overlap arbitrarily and there can be as many as needed. 

Let us manually add a few annotations to the document:


```python
# create and get an annotation set with the name "Set1"
annset = doc.annset("Set1")
```

Add an annotation to the set which refers to the first word in the document "This". The range of characters
for this word starts at offset 0 and the length of the annotation is 4, so the "start" offset is 0 and the "end" offset is 0+4=4. Note that the end offset always points to the offset *after* the last character of the range.


```python
annset.add(0,4,"Word",{"what": "our first annotation"})
```




    Annotation(0,4,Word,features=Features({'what': 'our first annotation'}),id=0)




```python
# Add more
annset.add(5,7,"Word",{"what": "our second annotation"})
annset.add(0,24,"Sentence",{"what": "our first sentence annotation"})
```




    Annotation(0,24,Sentence,features=Features({'what': 'our first sentence annotation'}),id=2)



If we visualize the document now, the newly created set "Set" is shown in the right part of
the display. It shows the different annotation types that exist in the set, and how many annotations
for each type are in the set. If you click the check box, the annotation ranges are shown in the 
text with the colour associated with the annotation type. You can then click on a range / annotation in the
text and the features of the annotation are shown in the lower part. 
To show the features for a different annotation click on the coloured range for the annotation in the text.
To show the document features, click on "Document".

If you have selected more than one type, a range can have more than one overlapping annotations. 
This is shown by mixing the colours. If you click at such a location, a dialog appears which lets you
select for which of the overlapping annotations you want to display the features. 


```python
doc
```





            <style>
              div#TJTSQZSFWH-wrapper: { color: black: !important; }
            </style>
            <div id="TJTSQZSFWH-wrapper">

<div>
<style>
#TJTSQZSFWH-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.TJTSQZSFWH-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.TJTSQZSFWH-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.TJTSQZSFWH-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.TJTSQZSFWH-label {
    margin-bottom: -15px;
    display: block;
}

.TJTSQZSFWH-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#TJTSQZSFWH-popup {
    display: none;
    colour: white;
    position: absolute;
    margin-top: 10%;
    margin-left: 10%;
    background: #ff88ff;
    width: 60%;
    height: 60%;
    z-index: 50;
    padding: 25px 25px 25px;
    border: 1px solid black;
    overflow: auto;
}

.TJTSQZSFWH-selection {
    margin-bottom: 5px;
}

.TJTSQZSFWH-featuretable {
    margin-top: 10px;
}

.TJTSQZSFWH-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.TJTSQZSFWH-fvalue {
    text-align: left !important;
}
</style>
  <div id="TJTSQZSFWH-content">
        <div id="TJTSQZSFWH-popup" style="display: none;">
        </div>
        <div class="TJTSQZSFWH-row" id="TJTSQZSFWH-row1" style="height:67vh; min-height:100px;">
            <div id="TJTSQZSFWH-text-wrapper" class="TJTSQZSFWH-col" style="width:70%;">
                <div class="TJTSQZSFWH-hdr" id="TJTSQZSFWH-dochdr"></div>
                <div id="TJTSQZSFWH-text">
                </div>
            </div>
            <div id="TJTSQZSFWH-chooser" class="TJTSQZSFWH-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="TJTSQZSFWH-row" id="TJTSQZSFWH-row2" style="height:30vh; min-height: 100px;">
            <div id="TJTSQZSFWH-details" class="TJTSQZSFWH-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.8/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="TJTSQZSFWH-data">
    {"annotation_sets": {"Set1": {"name": "detached-from:Set1", "annotations": [{"type": "Word", "start": 0, "end": 4, "id": 0, "features": {"what": "our first annotation"}}, {"type": "Word", "start": 5, "end": 7, "id": 1, "features": {"what": "our second annotation"}}, {"type": "Sentence", "start": 0, "end": 24, "id": 2, "features": {"what": "our first sentence annotation"}}], "next_annid": 3}}, "text": "This is a test document.\n\nIt contains just a few sentences. \nHere is a sentence that mentions a few named entities like \nthe persons Barack Obama or Ursula von der Leyen, locations\nlike New York City, Vienna or Beijing or companies like \nGoogle, UniCredit or Huawei. \n\nHere we include a URL https://gatenlp.github.io/python-gatenlp/ \nand a fake email address john.doe@hiscoolserver.com as well \nas #some #cool #hastags and a bunch of emojis like \ud83d\ude3d (a kissing cat),\n\ud83d\udc69\u200d\ud83c\udfeb (a woman teacher), \ud83e\uddec (DNA), \n\ud83e\uddd7 (a person climbing), \n\ud83d\udca9 (a pile of poo). \n\nHere we test a few different scripts, e.g. Hangul \ud55c\uae00 or \nsimplified Hanzi \u6c49\u5b57 or Farsi \u0641\u0627\u0631\u0633\u06cc which goes from right to left. \n\n\n", "features": {"loaded-from": "https://gatenlp.github.io/python-gatenlp/testdocument1.txt", "purpose": "test document for gatenlp", "someotherfeature": 22, "andanother": {"what": "a dict", "alist": [1, 2, 3, 4, 5]}}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("TJTSQZSFWH-");
    </script>
  </div>

            </div>





```python

```
