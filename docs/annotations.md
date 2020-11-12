# Annotations

See also: 
* [Python Documentation](pythondoc/gatenlp/annotation.html)

Annotations are objects that provide information about a span of text. In `gatenlp` annotations are used to identify tokens, entities, sentences, paragraphs, and other things: unlike in other NLP libraries, the same abstraction is used for everything that is about offset spans in a document. This abstraction is identical to what is used in Java GATE.

Annotations contain the following information:

* start offset (`ann.start`): the offset of the first character of the span
* end offset (`ann.end`): the offset after the last character of the span
* type (`ann.type`): some arbitrary name for the type of offset range represented, e.g. "Token", "Sentence", "Person"
* features (`ann.features`): arbitrary name/value pairs providing the information about the span, where name is a string and value is any JSON-serializable data type. 
* id (`ann.id`): the annotation id identifies the annotation uniquely within the containing [AnnotationSet](annotationsets). 

The normal way to create an annotation is by using the `AnnotationSet` method `add`:


```python
from gatenlp import Document, Annotation
doc = Document("Some test document")
annset = doc.annset()
ann = annset.add(2,4,"Token",{"lemma": "is"})
ann
# Out: Annotation(2,4,Token,id=1,features={'lemma': 'is'})
```




    Annotation(2,4,Token,features=Features({'lemma': 'is'}),id=0)



This creates an annotation of type "Token" starting with the character at offset 2 and ending with the character at offset 3 (the end offset is alwyas one after the last character). The annotation gets initialized with a single feature "lemma" which has the value "is". 

Once an annotation has been created, everything but the features is immutable. Trying to e.g. do `ann.start = 12` will raise an exception.

To change or set or remove a feature use the methods provided
by [Features](docs/pythondoc/gatenlp/features.html)

An annotation can also be directly created:


```python
ann2 = Annotation(2,4,"Token",annid=1,features={"lemma": "is"})
ann2
# Out: Annotation(2,4,Token,id=1,features={'lemma': 'is'})
```




    Annotation(2,4,Token,features=Features({'lemma': 'is'}),id=1)



However such a "free floating" annotation is probably not of much use and there is no way to add it directly to an annotation set. The method `annset.add_ann(ann)` can be used to add an anntotation that is a copy of `ann`. 

## Annotation span methods

There can be as many annotations for as many arbitrary spans as needed, and they can overlap arbitrarily.  There are several annotation methods which can be used to find out how exactly they overlap or are contained within each other.


```python
ann_tok1 = annset.add(0,4,"Token")
ann_tok2 = annset.add(5,13,"Token")
ann_all = annset.add(0,13,"Document")
ann_vowel1 = annset.add(1,2,"Vowel")
ann_vowel2 = annset.add(3,4,"Vowel")
```

Annotations have a "length" which is the number of characters annotated, i.e. the length of the annotated span:


```python
assert ann_tok1.length == 4
```

The ordering of annotations is by start offset, then annotation id.


```python
# does one annotation come before the other?
assert ann_tok1 < ann_tok2
# True
assert ann_tok1 < ann_vowel1
# True
assert ann_tok1 < ann_all
# True (annotations added later have a higher annotation id)
```

Checking for overlaps:


```python
assert not ann_tok1.isoverlapping(ann_tok2)

assert not ann_tok1.iscoextensive(ann_tok2)

assert ann_tok1.isoverlapping(ann_vowel1)

assert ann_tok1.iswithin(ann_all)

assert ann_tok1.iscovering(ann_vowel2)

assert ann_tok1.isbefore(ann_tok2)

assert not ann_tok1.isbefore(ann_tok2, immediately=True)

assert ann_tok1.gap(ann_tok2) == 1
```


```python
# show the document with those annotations in the notebook:
doc
```




<div><style>#DCBDLTMXSE-wrapper { color: black !important; }</style>
<div id="DCBDLTMXSE-wrapper">

<div>

<style>
#DCBDLTMXSE-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.DCBDLTMXSE-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.DCBDLTMXSE-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.DCBDLTMXSE-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.DCBDLTMXSE-label {
    margin-bottom: -15px;
    display: block;
}

.DCBDLTMXSE-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#DCBDLTMXSE-popup {
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

.DCBDLTMXSE-selection {
    margin-bottom: 5px;
}

.DCBDLTMXSE-featuretable {
    margin-top: 10px;
}

.DCBDLTMXSE-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.DCBDLTMXSE-fvalue {
    text-align: left !important;
}
</style>
  <div id="DCBDLTMXSE-content">
        <div id="DCBDLTMXSE-popup" style="display: none;">
        </div>
        <div class="DCBDLTMXSE-row" id="DCBDLTMXSE-row1" style="height:67vh; min-height:100px;">
            <div id="DCBDLTMXSE-text-wrapper" class="DCBDLTMXSE-col" style="width:70%;">
                <div class="DCBDLTMXSE-hdr" id="DCBDLTMXSE-dochdr"></div>
                <div id="DCBDLTMXSE-text">
                </div>
            </div>
            <div id="DCBDLTMXSE-chooser" class="DCBDLTMXSE-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="DCBDLTMXSE-row" id="DCBDLTMXSE-row2" style="height:30vh; min-height: 100px;">
            <div id="DCBDLTMXSE-details" class="DCBDLTMXSE-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>

    <script type="application/json" id="DCBDLTMXSE-data">
    {"annotation_sets": {"": {"name": "detached-from:", "annotations": [{"type": "Token", "start": 2, "end": 4, "id": 0, "features": {"lemma": "is"}}, {"type": "Token", "start": 0, "end": 4, "id": 1, "features": {}}, {"type": "Token", "start": 5, "end": 13, "id": 2, "features": {}}, {"type": "Document", "start": 0, "end": 13, "id": 3, "features": {}}, {"type": "Vowel", "start": 1, "end": 2, "id": 4, "features": {}}, {"type": "Vowel", "start": 3, "end": 4, "id": 5, "features": {}}], "next_annid": 6}}, "text": "Some test document", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("DCBDLTMXSE-");
    </script>
  </div>

</div></div>




```python

```
