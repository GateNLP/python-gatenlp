# Gazetteers





```python
import os
from gatenlp import Document
from gatenlp.processing.gazetteer import TokenGazetteer
from gatenlp.processing.tokenizer import NLTKTokenizer

# all the example files will be created in "./tmp"
if not os.path.exists("tmp"):
    os.mkdir("tmp")
```


```python

# 1) Create a gazetteer from a Python list 

gazlist = [
    ("Barack Obama", dict(url="https://en.wikipedia.org/wiki/Barack_Obama")),
    ("Obama", dict(url="https://en.wikipedia.org/wiki/Barack_Obama")),
    ("Donald Trump", dict(url="https://en.wikipedia.org/wiki/Donald_Trump")),
    ("Trump", dict(url="https://en.wikipedia.org/wiki/Donald_Trump")),
    ("George W. Bush", dict(url="https://en.wikipedia.org/wiki/George_W._Bush")),
    ("George Bush", dict(url="https://en.wikipedia.org/wiki/George_W._Bush")),
    ("Bush", dict(url="https://en.wikipedia.org/wiki/George_W._Bush")),
    ("Bill Clinton", dict(url="https://en.wikipedia.org/wiki/Bill_Clinton")),
    ("Clinton", dict(url="https://en.wikipedia.org/wiki/Bill_Clinton")),
]

# Document with some text mentioning some of the names
text = """Barack Obama was the 44th president of the US and he followed George W. Bush and
  was followed by Donald Trump. Before Bush, Bill Clinton was president."""
doc = Document(text)
doc
```




<div><style>#NAQCVNOVDP-wrapper { color: black !important; }</style>
<div id="NAQCVNOVDP-wrapper">

<div>
<style>
#NAQCVNOVDP-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.NAQCVNOVDP-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.NAQCVNOVDP-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.NAQCVNOVDP-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.NAQCVNOVDP-label {
    margin-bottom: -15px;
    display: block;
}

.NAQCVNOVDP-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#NAQCVNOVDP-popup {
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

.NAQCVNOVDP-selection {
    margin-bottom: 5px;
}

.NAQCVNOVDP-featuretable {
    margin-top: 10px;
}

.NAQCVNOVDP-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.NAQCVNOVDP-fvalue {
    text-align: left !important;
}
</style>
  <div id="NAQCVNOVDP-content">
        <div id="NAQCVNOVDP-popup" style="display: none;">
        </div>
        <div class="NAQCVNOVDP-row" id="NAQCVNOVDP-row1" style="height:67vh; min-height:100px;">
            <div id="NAQCVNOVDP-text-wrapper" class="NAQCVNOVDP-col" style="width:70%;">
                <div class="NAQCVNOVDP-hdr" id="NAQCVNOVDP-dochdr"></div>
                <div id="NAQCVNOVDP-text">
                </div>
            </div>
            <div id="NAQCVNOVDP-chooser" class="NAQCVNOVDP-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="NAQCVNOVDP-row" id="NAQCVNOVDP-row2" style="height:30vh; min-height: 100px;">
            <div id="NAQCVNOVDP-details" class="NAQCVNOVDP-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.11/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="NAQCVNOVDP-data">
    {"annotation_sets": {}, "text": "Barack Obama was the 44th president of the US and he followed George W. Bush and\n  was followed by Donald Trump. Before Bush, Bill Clinton was president.", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("NAQCVNOVDP-");
    </script>
  </div>

</div></div>




```python
# Tokenize the document, lets use an NLTK tokenizer
from nltk.tokenize.destructive import NLTKWordTokenizer

tokenizer = NLTKTokenizer(nltk_tokenizer=NLTKWordTokenizer(), out_set="", token_type="Token")
doc = tokenizer(doc)
doc
```




<div><style>#SAEOTPNANQ-wrapper { color: black !important; }</style>
<div id="SAEOTPNANQ-wrapper">

<div>
<style>
#SAEOTPNANQ-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.SAEOTPNANQ-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.SAEOTPNANQ-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.SAEOTPNANQ-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.SAEOTPNANQ-label {
    margin-bottom: -15px;
    display: block;
}

.SAEOTPNANQ-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#SAEOTPNANQ-popup {
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

.SAEOTPNANQ-selection {
    margin-bottom: 5px;
}

.SAEOTPNANQ-featuretable {
    margin-top: 10px;
}

.SAEOTPNANQ-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.SAEOTPNANQ-fvalue {
    text-align: left !important;
}
</style>
  <div id="SAEOTPNANQ-content">
        <div id="SAEOTPNANQ-popup" style="display: none;">
        </div>
        <div class="SAEOTPNANQ-row" id="SAEOTPNANQ-row1" style="height:67vh; min-height:100px;">
            <div id="SAEOTPNANQ-text-wrapper" class="SAEOTPNANQ-col" style="width:70%;">
                <div class="SAEOTPNANQ-hdr" id="SAEOTPNANQ-dochdr"></div>
                <div id="SAEOTPNANQ-text">
                </div>
            </div>
            <div id="SAEOTPNANQ-chooser" class="SAEOTPNANQ-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="SAEOTPNANQ-row" id="SAEOTPNANQ-row2" style="height:30vh; min-height: 100px;">
            <div id="SAEOTPNANQ-details" class="SAEOTPNANQ-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.11/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="SAEOTPNANQ-data">
    {"annotation_sets": {"": {"name": "detached-from:", "annotations": [{"type": "Token", "start": 0, "end": 6, "id": 0, "features": {}}, {"type": "Token", "start": 7, "end": 12, "id": 1, "features": {}}, {"type": "Token", "start": 13, "end": 16, "id": 2, "features": {}}, {"type": "Token", "start": 17, "end": 20, "id": 3, "features": {}}, {"type": "Token", "start": 21, "end": 25, "id": 4, "features": {}}, {"type": "Token", "start": 26, "end": 35, "id": 5, "features": {}}, {"type": "Token", "start": 36, "end": 38, "id": 6, "features": {}}, {"type": "Token", "start": 39, "end": 42, "id": 7, "features": {}}, {"type": "Token", "start": 43, "end": 45, "id": 8, "features": {}}, {"type": "Token", "start": 46, "end": 49, "id": 9, "features": {}}, {"type": "Token", "start": 50, "end": 52, "id": 10, "features": {}}, {"type": "Token", "start": 53, "end": 61, "id": 11, "features": {}}, {"type": "Token", "start": 62, "end": 68, "id": 12, "features": {}}, {"type": "Token", "start": 69, "end": 71, "id": 13, "features": {}}, {"type": "Token", "start": 72, "end": 76, "id": 14, "features": {}}, {"type": "Token", "start": 77, "end": 80, "id": 15, "features": {}}, {"type": "Token", "start": 83, "end": 86, "id": 16, "features": {}}, {"type": "Token", "start": 87, "end": 95, "id": 17, "features": {}}, {"type": "Token", "start": 96, "end": 98, "id": 18, "features": {}}, {"type": "Token", "start": 99, "end": 105, "id": 19, "features": {}}, {"type": "Token", "start": 106, "end": 112, "id": 20, "features": {}}, {"type": "Token", "start": 113, "end": 119, "id": 21, "features": {}}, {"type": "Token", "start": 120, "end": 124, "id": 22, "features": {}}, {"type": "Token", "start": 124, "end": 125, "id": 23, "features": {}}, {"type": "Token", "start": 126, "end": 130, "id": 24, "features": {}}, {"type": "Token", "start": 131, "end": 138, "id": 25, "features": {}}, {"type": "Token", "start": 139, "end": 142, "id": 26, "features": {}}, {"type": "Token", "start": 143, "end": 152, "id": 27, "features": {}}, {"type": "Token", "start": 152, "end": 153, "id": 28, "features": {}}], "next_annid": 29}}, "text": "Barack Obama was the 44th president of the US and he followed George W. Bush and\n  was followed by Donald Trump. Before Bush, Bill Clinton was president.", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("SAEOTPNANQ-");
    </script>
  </div>

</div></div>




```python

# Tokenize the strings from our gazetteer list as well

def text2tokenstrings(text):
    tmpdoc = Document(text)
    tokenizer(tmpdoc)
    tokens = list(tmpdoc.annset().with_type("Token"))
    return [tmpdoc[tok] for tok in tokens]

gazlist = [(text2tokenstrings(txt), feats) for txt, feats in gazlist]
gazlist
    
```




    [(['Barack', 'Obama'], {'url': 'https://en.wikipedia.org/wiki/Barack_Obama'}),
     (['Obama'], {'url': 'https://en.wikipedia.org/wiki/Barack_Obama'}),
     (['Donald', 'Trump'], {'url': 'https://en.wikipedia.org/wiki/Donald_Trump'}),
     (['Trump'], {'url': 'https://en.wikipedia.org/wiki/Donald_Trump'}),
     (['George', 'W.', 'Bush'],
      {'url': 'https://en.wikipedia.org/wiki/George_W._Bush'}),
     (['George', 'Bush'], {'url': 'https://en.wikipedia.org/wiki/George_W._Bush'}),
     (['Bush'], {'url': 'https://en.wikipedia.org/wiki/George_W._Bush'}),
     (['Bill', 'Clinton'], {'url': 'https://en.wikipedia.org/wiki/Bill_Clinton'}),
     (['Clinton'], {'url': 'https://en.wikipedia.org/wiki/Bill_Clinton'})]




```python
# Create the gazetter and apply it to the document

gazetteer = TokenGazetteer(gazlist, fmt="gazlist", all=True, skip=False, outset="", outtype="Lookup",
                          annset="", tokentype="Token")

doc = gazetteer(doc)
doc
```




<div><style>#IPSPADWJVQ-wrapper { color: black !important; }</style>
<div id="IPSPADWJVQ-wrapper">

<div>
<style>
#IPSPADWJVQ-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.IPSPADWJVQ-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.IPSPADWJVQ-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.IPSPADWJVQ-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.IPSPADWJVQ-label {
    margin-bottom: -15px;
    display: block;
}

.IPSPADWJVQ-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#IPSPADWJVQ-popup {
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

.IPSPADWJVQ-selection {
    margin-bottom: 5px;
}

.IPSPADWJVQ-featuretable {
    margin-top: 10px;
}

.IPSPADWJVQ-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.IPSPADWJVQ-fvalue {
    text-align: left !important;
}
</style>
  <div id="IPSPADWJVQ-content">
        <div id="IPSPADWJVQ-popup" style="display: none;">
        </div>
        <div class="IPSPADWJVQ-row" id="IPSPADWJVQ-row1" style="height:67vh; min-height:100px;">
            <div id="IPSPADWJVQ-text-wrapper" class="IPSPADWJVQ-col" style="width:70%;">
                <div class="IPSPADWJVQ-hdr" id="IPSPADWJVQ-dochdr"></div>
                <div id="IPSPADWJVQ-text">
                </div>
            </div>
            <div id="IPSPADWJVQ-chooser" class="IPSPADWJVQ-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="IPSPADWJVQ-row" id="IPSPADWJVQ-row2" style="height:30vh; min-height: 100px;">
            <div id="IPSPADWJVQ-details" class="IPSPADWJVQ-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.11/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="IPSPADWJVQ-data">
    {"annotation_sets": {"": {"name": "detached-from:", "annotations": [{"type": "Token", "start": 0, "end": 6, "id": 0, "features": {}}, {"type": "Token", "start": 7, "end": 12, "id": 1, "features": {}}, {"type": "Token", "start": 13, "end": 16, "id": 2, "features": {}}, {"type": "Token", "start": 17, "end": 20, "id": 3, "features": {}}, {"type": "Token", "start": 21, "end": 25, "id": 4, "features": {}}, {"type": "Token", "start": 26, "end": 35, "id": 5, "features": {}}, {"type": "Token", "start": 36, "end": 38, "id": 6, "features": {}}, {"type": "Token", "start": 39, "end": 42, "id": 7, "features": {}}, {"type": "Token", "start": 43, "end": 45, "id": 8, "features": {}}, {"type": "Token", "start": 46, "end": 49, "id": 9, "features": {}}, {"type": "Token", "start": 50, "end": 52, "id": 10, "features": {}}, {"type": "Token", "start": 53, "end": 61, "id": 11, "features": {}}, {"type": "Token", "start": 62, "end": 68, "id": 12, "features": {}}, {"type": "Token", "start": 69, "end": 71, "id": 13, "features": {}}, {"type": "Token", "start": 72, "end": 76, "id": 14, "features": {}}, {"type": "Token", "start": 77, "end": 80, "id": 15, "features": {}}, {"type": "Token", "start": 83, "end": 86, "id": 16, "features": {}}, {"type": "Token", "start": 87, "end": 95, "id": 17, "features": {}}, {"type": "Token", "start": 96, "end": 98, "id": 18, "features": {}}, {"type": "Token", "start": 99, "end": 105, "id": 19, "features": {}}, {"type": "Token", "start": 106, "end": 112, "id": 20, "features": {}}, {"type": "Token", "start": 113, "end": 119, "id": 21, "features": {}}, {"type": "Token", "start": 120, "end": 124, "id": 22, "features": {}}, {"type": "Token", "start": 124, "end": 125, "id": 23, "features": {}}, {"type": "Token", "start": 126, "end": 130, "id": 24, "features": {}}, {"type": "Token", "start": 131, "end": 138, "id": 25, "features": {}}, {"type": "Token", "start": 139, "end": 142, "id": 26, "features": {}}, {"type": "Token", "start": 143, "end": 152, "id": 27, "features": {}}, {"type": "Token", "start": 152, "end": 153, "id": 28, "features": {}}, {"type": "Lookup", "start": 0, "end": 12, "id": 29, "features": {"url": "https://en.wikipedia.org/wiki/Barack_Obama"}}, {"type": "Lookup", "start": 7, "end": 12, "id": 30, "features": {"url": "https://en.wikipedia.org/wiki/Barack_Obama"}}, {"type": "Lookup", "start": 62, "end": 76, "id": 31, "features": {"url": "https://en.wikipedia.org/wiki/George_W._Bush"}}, {"type": "Lookup", "start": 72, "end": 76, "id": 32, "features": {"url": "https://en.wikipedia.org/wiki/George_W._Bush"}}, {"type": "Lookup", "start": 120, "end": 124, "id": 33, "features": {"url": "https://en.wikipedia.org/wiki/George_W._Bush"}}, {"type": "Lookup", "start": 126, "end": 138, "id": 34, "features": {"url": "https://en.wikipedia.org/wiki/Bill_Clinton"}}, {"type": "Lookup", "start": 131, "end": 138, "id": 35, "features": {"url": "https://en.wikipedia.org/wiki/Bill_Clinton"}}], "next_annid": 36}}, "text": "Barack Obama was the 44th president of the US and he followed George W. Bush and\n  was followed by Donald Trump. Before Bush, Bill Clinton was president.", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("IPSPADWJVQ-");
    </script>
  </div>

</div></div>


