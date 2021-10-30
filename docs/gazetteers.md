# Gazetteers

Gazetteers make it easy to find matches in a document from a large list of gazetteer entries. Entries can be associated with arbitrary features, and when a match is found, an annotation is created with the features related to the gazetteer entry. `gatenlp` currently supports the following gazetteer annotators:

* `StringGazetteer`: match the document text against a gazetteer list of string entries
* `TokenGazetteer`: match an annotation (token) sequence in the document against a gazetteer list of entries, where each entry is a sequence of token strings



```python
import os
from gatenlp import Document
from gatenlp.processing.gazetteer import TokenGazetteer, StringGazetteer
from gatenlp.processing.tokenizer import NLTKTokenizer

# all the example files will be created in "./tmp"
if not os.path.exists("tmp"):
    os.mkdir("tmp")
```

## StringGazetteer

The main features of the `StringGazetteer`

* match arbitrary strings in the document text
* matches a single space in an gazetteer entry against any number of whitespace characters in the document text
* can use a list of characters, a function, or annotations to define what should be treated as whitespace
* optionally will not match across "split" characters
* can use a list of characters, a function, or annotations to define what should be treated as split characters
* optionally only matches from word starting and/or to word ending positions
* uses annotations to define where word start/end locations are in the document
* can load GATE gazetteer files
* can load the gazetteer from Python a python list

#### Create a gazetteer from a Python list

Each gazetteer entry is a tuple, where the first element is the string to match and the second element is a dictionary with arbitrary features. When an entry contains leading or trailing whitespace, by default it is removed and multiple whitespace characters within the entry are replaced by a single space internally (this can be disabled with the `ws_clean=False` parameter if the gazetteer entries are already properly cleaned)



```python
gazlist1 = [
    ("Barack Obama", dict(url="https://en.wikipedia.org/wiki/Barack_Obama")),
    ("Obama", dict(url="https://en.wikipedia.org/wiki/Barack_Obama")),
    ("Donald Trump", dict(url="https://en.wikipedia.org/wiki/Donald_Trump")),
    ("Trump", dict(url="https://en.wikipedia.org/wiki/Donald_Trump")),
    ("George W. Bush", dict(url="https://en.wikipedia.org/wiki/George_W._Bush")),
    ("George Bush", dict(url="https://en.wikipedia.org/wiki/George_W._Bush")),
    ("Bush", dict(url="https://en.wikipedia.org/wiki/George_W._Bush")),
    ("    Bill        Clinton   ", dict(url="https://en.wikipedia.org/wiki/Bill_Clinton")),
    ("Clinton", dict(url="https://en.wikipedia.org/wiki/Bill_Clinton")),
]

# Document with some text mentioning some of the names in the gazeteer for testing
text = """Barack Obama was the 44th president of the US and he followed George W. Bush and
  was followed by Donald Trump. Before Bush, Bill Clinton was president.
  Also, lets include a sentence about South Korea which is called 대한민국 in Korean.
  And a sentence with the full name of Iran in Farsi: جمهوری اسلامی ایران and also with 
  just the word "Iran" in Farsi: ایران 
  Also barack obama in all lower case and SOUTH KOREA in all upper case
  """
doc = Document(text)
doc
```




<div><style>#BAALRJCXUJ-wrapper { color: black !important; }</style>
<div id="BAALRJCXUJ-wrapper">

<div>
<style>
#BAALRJCXUJ-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.BAALRJCXUJ-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.BAALRJCXUJ-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.BAALRJCXUJ-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.BAALRJCXUJ-label {
    margin-bottom: -15px;
    display: block;
}

.BAALRJCXUJ-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#BAALRJCXUJ-popup {
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

.BAALRJCXUJ-selection {
    margin-bottom: 5px;
}

.BAALRJCXUJ-featuretable {
    margin-top: 10px;
}

.BAALRJCXUJ-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.BAALRJCXUJ-fvalue {
    text-align: left !important;
}
</style>
  <div id="BAALRJCXUJ-content">
        <div id="BAALRJCXUJ-popup" style="display: none;">
        </div>
        <div class="BAALRJCXUJ-row" id="BAALRJCXUJ-row1" style="max-height: 20em; min-height:5em;">
            <div id="BAALRJCXUJ-text-wrapper" class="BAALRJCXUJ-col" style="width:70%;">
                <div class="BAALRJCXUJ-hdr" id="BAALRJCXUJ-dochdr"></div>
                <div id="BAALRJCXUJ-text" style="">
                </div>
            </div>
            <div id="BAALRJCXUJ-chooser" class="BAALRJCXUJ-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="BAALRJCXUJ-row" id="BAALRJCXUJ-row2" style="max-height: 14em; min-height: 3em;">
            <div id="BAALRJCXUJ-details" class="BAALRJCXUJ-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>

    <script type="text/javascript">
    let BAALRJCXUJ_data = {"annotation_sets": {}, "text": "Barack Obama was the 44th president of the US and he followed George W. Bush and\n  was followed by Donald Trump. Before Bush, Bill Clinton was president.\n  Also, lets include a sentence about South Korea which is called \ub300\ud55c\ubbfc\uad6d in Korean.\n  And a sentence with the full name of Iran in Farsi: \u062c\u0645\u0647\u0648\u0631\u06cc \u0627\u0633\u0644\u0627\u0645\u06cc \u0627\u06cc\u0631\u0627\u0646 and also with \n  just the word \"Iran\" in Farsi: \u0627\u06cc\u0631\u0627\u0646 \n  Also barack obama in all lower case and SOUTH KOREA in all upper case\n  ", "features": {}, "offset_type": "j", "name": ""} ; 
    new gatenlpDocView(new gatenlpDocRep(BAALRJCXUJ_data), "BAALRJCXUJ-").init();
    </script>
  </div>

</div></div>



### Create the StringGazetteer annotator 

In the following example we create the StringGazetteer and specify the source and the format of the source to also load some gazetteer entries into it. This is not required, gazetteer entries can also be added later (see below)


```python
gaz1 = StringGazetteer(source=gazlist1, source_fmt="gazlist")
```

The StringGazetteer instance is a gatenlp annotator, but can also be used to lookup the information for an entry 
or check if an entry is in the gazetteer.


```python
print("Entries:     ", len(gaz1))
print("Entry 'Trump': ", gaz1["Trump"])
print("Entry 'Bill Clinton': ", gaz1.get("Bill Clinton"))
print("Contains 'Bush':", "Bush" in gaz1)
```

    Entries:      9
    Entry 'Trump':  [{'url': 'https://en.wikipedia.org/wiki/Donald_Trump'}]
    Entry 'Bill Clinton':  [{'url': 'https://en.wikipedia.org/wiki/Bill_Clinton'}]
    Contains 'Bush': True


Gazetteer entries can also be added with the `add` and `append` methods. That way the gazetteer can be 
created from several different sources.

Every time gazetteer entries are loaded, it is possible to specify features which should get added to all 
entries of that list. 

Let us create a new list and specify some features common to all entries of this list and add it to the gazetteer:


```python
gazlist2 = [
    ("United States", dict(url="https://en.wikipedia.org/wiki/United_States")),
    ("US", dict(url="https://en.wikipedia.org/wiki/United_States")),
    ("United Kingdom", dict(url="https://en.wikipedia.org/wiki/United_Kingdom")),
    ("UK", dict(url="https://en.wikipedia.org/wiki/United_Kingdom")),    
    ("Austria", dict(url="https://en.wikipedia.org/wiki/Austria")),
    ("South Korea", dict(url="https://en.wikipedia.org/wiki/South_Korea")),
    ("대한민국", dict(url="https://en.wikipedia.org/wiki/South_Korea")),
    ("Iran", dict(url="https://en.wikipedia.org/wiki/Iran")),
    ("جمهوری اسلامی ایران", dict(url="https://en.wikipedia.org/wiki/Iran")),
    ("ایران", dict(url="https://en.wikipedia.org/wiki/Iran")),
]

# Note: if this cell gets executed several times, the data stored with each gazetteer entry gets  
# extended by a new dictionary of features!
# In general, there can be arbitrary many feature dictionaries for each entry which can be used to 
# store the different sets of information for different entities which share the same name.
gaz1.append(source=gazlist2, source_fmt="gazlist", list_features=dict(type="country"))

print("Entries:     ", len(gaz1))
print("Entry 'ایران': ", gaz1["ایران"])
print("Entry 'South Korea': ", gaz1["South Korea"])
```

    Entries:      19
    Entry 'ایران':  [{'url': 'https://en.wikipedia.org/wiki/Iran', 'type': 'country'}]
    Entry 'South Korea':  [{'url': 'https://en.wikipedia.org/wiki/South_Korea', 'type': 'country'}]


There are also methods to check if there is a match at some specific position in some text, to find the next match in some text, and to find all matches in some text:


```python
# methods match and find return a tuple with a list of StringGazetteerMatch objects describing all matches
# as the first element and the length of the longest of the matches at the second element, the find method returns
# the location of the match as the third element in the tuple
print("Check for a match in the document text at position 0: ", gaz1.match(doc.text, start=0))
print("Check for a match in the document text at position 1: ", gaz1.match(doc.text, start=1))
print("Find the next match from position 3", gaz1.find(doc.text, start=3))
# the find_all method does not return a tuple, but a generator of tuples:
print("Find all matches from position 340", list(gaz1.find_all(doc.text, start=340)))
```

    Check for a match in the document text at position 0:  ([StringGazetteerMatch(start=0, end=12, match='Barack Obama', data=[{'url': 'https://en.wikipedia.org/wiki/Barack_Obama'}], listidxs=[0])], 12)
    Check for a match in the document text at position 1:  ([], 0)
    Find the next match from position 3 ([StringGazetteerMatch(start=7, end=12, match='Obama', data=[{'url': 'https://en.wikipedia.org/wiki/Barack_Obama'}], listidxs=[0])], 5, 7)
    Find all matches from position 340 [StringGazetteerMatch(start=342, end=346, match='Iran', data=[{'url': 'https://en.wikipedia.org/wiki/Iran'}], listidxs=[1]), StringGazetteerMatch(start=358, end=363, match='ایران', data=[{'url': 'https://en.wikipedia.org/wiki/Iran'}], listidxs=[1])]


To annotate a document with the matches found in the gazetteer, the StringGazetteer instance can be 
used as an annotator. By default, matches can occur anywhere in the document, non-whitespace characters must
match exactly and no special split characters are recognized (so matches can occur across newline characters 
and sentence boundaries)

By default, annotations of type "Lookup" are created in the default set. The features of the annotation are set
to the information from the gazetteer entry and the list. If a gazetteer entry was added several times, separate
annotations are created for each information that was added for the gazetteer string.


```python
doc.annset().clear()
doc = gaz1(doc)
doc
```




<div><style>#TAUMMIFXOM-wrapper { color: black !important; }</style>
<div id="TAUMMIFXOM-wrapper">

<div>
<style>
#TAUMMIFXOM-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.TAUMMIFXOM-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.TAUMMIFXOM-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.TAUMMIFXOM-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.TAUMMIFXOM-label {
    margin-bottom: -15px;
    display: block;
}

.TAUMMIFXOM-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#TAUMMIFXOM-popup {
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

.TAUMMIFXOM-selection {
    margin-bottom: 5px;
}

.TAUMMIFXOM-featuretable {
    margin-top: 10px;
}

.TAUMMIFXOM-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.TAUMMIFXOM-fvalue {
    text-align: left !important;
}
</style>
  <div id="TAUMMIFXOM-content">
        <div id="TAUMMIFXOM-popup" style="display: none;">
        </div>
        <div class="TAUMMIFXOM-row" id="TAUMMIFXOM-row1" style="max-height: 20em; min-height:5em;">
            <div id="TAUMMIFXOM-text-wrapper" class="TAUMMIFXOM-col" style="width:70%;">
                <div class="TAUMMIFXOM-hdr" id="TAUMMIFXOM-dochdr"></div>
                <div id="TAUMMIFXOM-text" style="">
                </div>
            </div>
            <div id="TAUMMIFXOM-chooser" class="TAUMMIFXOM-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="TAUMMIFXOM-row" id="TAUMMIFXOM-row2" style="max-height: 14em; min-height: 3em;">
            <div id="TAUMMIFXOM-details" class="TAUMMIFXOM-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>

    <script type="text/javascript">
    let TAUMMIFXOM_data = {"annotation_sets": {"": {"name": "detached-from:", "annotations": [{"type": "Lookup", "start": 0, "end": 12, "id": 0, "features": {"url": "https://en.wikipedia.org/wiki/Barack_Obama"}}, {"type": "Lookup", "start": 7, "end": 12, "id": 1, "features": {"url": "https://en.wikipedia.org/wiki/Barack_Obama"}}, {"type": "Lookup", "start": 43, "end": 45, "id": 2, "features": {"type": "country", "url": "https://en.wikipedia.org/wiki/United_States"}}, {"type": "Lookup", "start": 62, "end": 76, "id": 3, "features": {"url": "https://en.wikipedia.org/wiki/George_W._Bush"}}, {"type": "Lookup", "start": 72, "end": 76, "id": 4, "features": {"url": "https://en.wikipedia.org/wiki/George_W._Bush"}}, {"type": "Lookup", "start": 99, "end": 111, "id": 5, "features": {"url": "https://en.wikipedia.org/wiki/Donald_Trump"}}, {"type": "Lookup", "start": 106, "end": 111, "id": 6, "features": {"url": "https://en.wikipedia.org/wiki/Donald_Trump"}}, {"type": "Lookup", "start": 120, "end": 124, "id": 7, "features": {"url": "https://en.wikipedia.org/wiki/George_W._Bush"}}, {"type": "Lookup", "start": 126, "end": 138, "id": 8, "features": {"url": "https://en.wikipedia.org/wiki/Bill_Clinton"}}, {"type": "Lookup", "start": 131, "end": 138, "id": 9, "features": {"url": "https://en.wikipedia.org/wiki/Bill_Clinton"}}, {"type": "Lookup", "start": 192, "end": 203, "id": 10, "features": {"type": "country", "url": "https://en.wikipedia.org/wiki/South_Korea"}}, {"type": "Lookup", "start": 220, "end": 224, "id": 11, "features": {"type": "country", "url": "https://en.wikipedia.org/wiki/South_Korea"}}, {"type": "Lookup", "start": 275, "end": 279, "id": 12, "features": {"type": "country", "url": "https://en.wikipedia.org/wiki/Iran"}}, {"type": "Lookup", "start": 290, "end": 309, "id": 13, "features": {"type": "country", "url": "https://en.wikipedia.org/wiki/Iran"}}, {"type": "Lookup", "start": 304, "end": 309, "id": 14, "features": {"type": "country", "url": "https://en.wikipedia.org/wiki/Iran"}}, {"type": "Lookup", "start": 342, "end": 346, "id": 15, "features": {"type": "country", "url": "https://en.wikipedia.org/wiki/Iran"}}, {"type": "Lookup", "start": 358, "end": 363, "id": 16, "features": {"type": "country", "url": "https://en.wikipedia.org/wiki/Iran"}}], "next_annid": 17}}, "text": "Barack Obama was the 44th president of the US and he followed George W. Bush and\n  was followed by Donald Trump. Before Bush, Bill Clinton was president.\n  Also, lets include a sentence about South Korea which is called \ub300\ud55c\ubbfc\uad6d in Korean.\n  And a sentence with the full name of Iran in Farsi: \u062c\u0645\u0647\u0648\u0631\u06cc \u0627\u0633\u0644\u0627\u0645\u06cc \u0627\u06cc\u0631\u0627\u0646 and also with \n  just the word \"Iran\" in Farsi: \u0627\u06cc\u0631\u0627\u0646 \n  Also barack obama in all lower case and SOUTH KOREA in all upper case\n  ", "features": {}, "offset_type": "j", "name": ""} ; 
    new gatenlpDocView(new gatenlpDocRep(TAUMMIFXOM_data), "TAUMMIFXOM-").init();
    </script>
  </div>

</div></div>



### StringGazetteer parameters

The parameters for the StringGazetteer constructor can be used to change the behaviour of the gazetteer in many ways. The parameters related to loading gazetteer entries can also be specified with the `append` method. 

Parameters to influence how annotations for matches are created:
* `outset_name`: which annotation set to place the annotations in
* `ann_type`: the annotation type to use, default is "Lookup". Note that if a list is loaded, it is possible to 
  specify a list-specific annotation type.

Parameters to influence how the matches are carried out through annotations in the document. If a parameter is None,
the match is not influenced by that kind of annotations, but could be influenced by other parameters (see below):
* `start_type`: the type of annotations used to identify where matches can start (e.g. Token annotations)
* `end_type`: the type of annotations used to identify where atches can end
* `ws_type`: the type of annotations which indicate whitespace in the document. 
* `split_type`: the type of annotations which indicate a split, i.e. something which should not be part of a match
* `annset_name`: the name of the annotation set where all the annotations above are expceted

Other parameters to influence how matches are carried out:
* `ws_chars`: if `ws_type` is not specified, can be used to change which characters should be considered whitespace by specifying a string of those characters or a callable that returns True or False when passed a character
* `split_chars`: if `split_type` is not specified, can be used to change which characters should be considered split characters by specifying a string of those characters or a callable that returns True or False when passed a character
* `map_chars`: how to map characters when storing a gazetteer entry or accessing the text to match: either a callable that maps a single character to a single character or one of the strings "lower" or "upper"
* `ws_clean`: if True (the default) enables trimming and white-space normalization of gazetteer entries when loading, if False, assumes that this has been correctly done already.

Parameters that influence how gazetteer data is loaded:
* `source`: what to load. This is either the path to a file (a string) or a list with gazetteer entries, depending on the `source_fmt` 
* `source_fmt`: specifies what format the gazetteer data to load is in
* `source_encoding`: the encoding if data gets loaded from a file
* `source_sep`: the separator character if the format is "gate-def". For legacy GATE gazetteer files, ":" should be used. 
* `list_features`: a dict of features to assign to all entries of a list that gets loaded 
* `list_type`: if a list gets loaded, this can be used to override the annotation type of annotations that get created for matches, if None, the type specified via `ann_type` or the default "Lookup" is used
* `list_nr`: can be used to add list features to the list features of an already loaded list and add the gazetteer entries to that list



```python

```


```python

```


```python

```


```python

```


```python

```


```python

```


```python

```


```python

```


```python
# Tokenize the document, lets use an NLTK tokenizer
from nltk.tokenize.destructive import NLTKWordTokenizer

tokenizer = NLTKTokenizer(nltk_tokenizer=NLTKWordTokenizer(), out_set="", token_type="Token")
doc = tokenizer(doc)
doc
```


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


```python
# Create the gazetter and apply it to the document

gazetteer = TokenGazetteer(gazlist, fmt="gazlist", all=True, skip=False, outset="", outtype="Lookup",
                          annset="", tokentype="Token")

doc = gazetteer(doc)
doc
```
