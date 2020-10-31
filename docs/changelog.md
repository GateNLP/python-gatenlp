# ChangeLog 

The ChangeLog can be used to record all changes made to a document. This is primarily used for the Java GATE "Python" plugin (http://gatenlp.github.io/gateplugin-Python/): this plugin sends a document from Java to Python by converting it to the Python representation where it is then modified and the modifications are recorded in a ChangeLog instance. The ChangeLog instance is sent back to Java and the changes are applied to the original Java GATE document. 

This can also be used in other sitations e.g. when the same document is annotated in parallel by several separate processes (e.g. different kinds of annotations or different parts of the document getting annotated): each process can then send the changelog to the process responsible to apply it to a single document. 

Changes to a document are only recorded if a ChangeLog instance is set for the document, this does not happen by default. 


```python
from gatenlp import Document, ChangeLog
from IPython.display import display
```


```python
# Create a two documents from some text
text = "This is some text"
doc1 = Document(text)
doc2 = Document(text)

# Create a ChangeLog instance
chlog = ChangeLog()

print("Empty ChangeLog:", chlog)

# Make doc1 use a ChangeLog
doc1.changelog = chlog

```

    Empty ChangeLog: ChangeLog([])



```python
# Create a few annotations and features

doc1.features["feature1"] = "some value"
defset = doc1.annset()
ann1 = defset.add(0,4,"SomeType", features={"annfeature1": 1, "annfeature2": 2})
ann2 = defset.add(5,7,"SomeType")
ann3 = defset.add(8,12,"SomeType")
# remove the second annotation
#defset.remove(ann2)
# add a feature to the first annotation
ann1.features["annfeature3"] = 3
# update a feature
ann1.features["annfeature1"] = 11

# show the ChangeLog
print(chlog)
```

    ChangeLog([{'command': 'doc-feature:set', 'feature': 'feature1', 'value': 'some value'},{'command': 'annotations:add', 'set': ''},{'command': 'annotation:add', 'set': '', 'start': 0, 'end': 4, 'type': 'SomeType', 'features': {'annfeature1': 1, 'annfeature2': 2}, 'id': 0},{'command': 'annotation:add', 'set': '', 'start': 5, 'end': 7, 'type': 'SomeType', 'features': {}, 'id': 1},{'command': 'annotation:add', 'set': '', 'start': 8, 'end': 12, 'type': 'SomeType', 'features': {}, 'id': 2},{'command': 'ann-feature:set', 'type': 'annotation', 'set': '', 'id': 0, 'feature': 'annfeature3', 'value': 3},{'command': 'ann-feature:set', 'type': 'annotation', 'set': '', 'id': 0, 'feature': 'annfeature1', 'value': 11}])



```python
# The changelog really just contains a list of dictionaries, each describing some action
# print the list of actions a bit more nicely
for action in chlog.changes:
    print(action)
```

    {'command': 'doc-feature:set', 'feature': 'feature1', 'value': 'some value'}
    {'command': 'annotations:add', 'set': ''}
    {'command': 'annotation:add', 'set': '', 'start': 0, 'end': 4, 'type': 'SomeType', 'features': {'annfeature1': 1, 'annfeature2': 2}, 'id': 0}
    {'command': 'annotation:add', 'set': '', 'start': 5, 'end': 7, 'type': 'SomeType', 'features': {}, 'id': 1}
    {'command': 'annotation:add', 'set': '', 'start': 8, 'end': 12, 'type': 'SomeType', 'features': {}, 'id': 2}
    {'command': 'ann-feature:set', 'type': 'annotation', 'set': '', 'id': 0, 'feature': 'annfeature3', 'value': 3}
    {'command': 'ann-feature:set', 'type': 'annotation', 'set': '', 'id': 0, 'feature': 'annfeature1', 'value': 11}



```python
# Show doc1 and doc2 

print("doc1")
display(doc1)

print("doc2")
display(doc2)
```

    doc1



<div><style>#AJMSEJOLGI-wrapper { color: black !important; }</style>
<div id="AJMSEJOLGI-wrapper">

<div>
<style>
#AJMSEJOLGI-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.AJMSEJOLGI-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.AJMSEJOLGI-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.AJMSEJOLGI-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.AJMSEJOLGI-label {
    margin-bottom: -15px;
    display: block;
}

.AJMSEJOLGI-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#AJMSEJOLGI-popup {
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

.AJMSEJOLGI-selection {
    margin-bottom: 5px;
}

.AJMSEJOLGI-featuretable {
    margin-top: 10px;
}

.AJMSEJOLGI-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.AJMSEJOLGI-fvalue {
    text-align: left !important;
}
</style>
  <div id="AJMSEJOLGI-content">
        <div id="AJMSEJOLGI-popup" style="display: none;">
        </div>
        <div class="AJMSEJOLGI-row" id="AJMSEJOLGI-row1" style="height:67vh; min-height:100px;">
            <div id="AJMSEJOLGI-text-wrapper" class="AJMSEJOLGI-col" style="width:70%;">
                <div class="AJMSEJOLGI-hdr" id="AJMSEJOLGI-dochdr"></div>
                <div id="AJMSEJOLGI-text">
                </div>
            </div>
            <div id="AJMSEJOLGI-chooser" class="AJMSEJOLGI-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="AJMSEJOLGI-row" id="AJMSEJOLGI-row2" style="height:30vh; min-height: 100px;">
            <div id="AJMSEJOLGI-details" class="AJMSEJOLGI-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.11/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="AJMSEJOLGI-data">
    {"annotation_sets": {"": {"name": "detached-from:", "annotations": [{"type": "SomeType", "start": 0, "end": 4, "id": 0, "features": {"annfeature1": 11, "annfeature2": 2, "annfeature3": 3}}, {"type": "SomeType", "start": 5, "end": 7, "id": 1, "features": {}}, {"type": "SomeType", "start": 8, "end": 12, "id": 2, "features": {}}], "next_annid": 3}}, "text": "This is some text", "features": {"feature1": "some value"}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("AJMSEJOLGI-");
    </script>
  </div>

</div></div>


    doc2



<div><style>#HUIUJMVRXB-wrapper { color: black !important; }</style>
<div id="HUIUJMVRXB-wrapper">

<div>
<style>
#HUIUJMVRXB-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.HUIUJMVRXB-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.HUIUJMVRXB-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.HUIUJMVRXB-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.HUIUJMVRXB-label {
    margin-bottom: -15px;
    display: block;
}

.HUIUJMVRXB-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#HUIUJMVRXB-popup {
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

.HUIUJMVRXB-selection {
    margin-bottom: 5px;
}

.HUIUJMVRXB-featuretable {
    margin-top: 10px;
}

.HUIUJMVRXB-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.HUIUJMVRXB-fvalue {
    text-align: left !important;
}
</style>
  <div id="HUIUJMVRXB-content">
        <div id="HUIUJMVRXB-popup" style="display: none;">
        </div>
        <div class="HUIUJMVRXB-row" id="HUIUJMVRXB-row1" style="height:67vh; min-height:100px;">
            <div id="HUIUJMVRXB-text-wrapper" class="HUIUJMVRXB-col" style="width:70%;">
                <div class="HUIUJMVRXB-hdr" id="HUIUJMVRXB-dochdr"></div>
                <div id="HUIUJMVRXB-text">
                </div>
            </div>
            <div id="HUIUJMVRXB-chooser" class="HUIUJMVRXB-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="HUIUJMVRXB-row" id="HUIUJMVRXB-row2" style="height:30vh; min-height: 100px;">
            <div id="HUIUJMVRXB-details" class="HUIUJMVRXB-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.11/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="HUIUJMVRXB-data">
    {"annotation_sets": {}, "text": "This is some text", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("HUIUJMVRXB-");
    </script>
  </div>

</div></div>



```python
# Apply the changelog to doc2 and show it: 
# the second document now has the same features and annotations as the first one
doc2.apply_changes(chlog)
display(doc2)
```


<div><style>#KYYSPBFCGD-wrapper { color: black !important; }</style>
<div id="KYYSPBFCGD-wrapper">

<div>
<style>
#KYYSPBFCGD-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.KYYSPBFCGD-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.KYYSPBFCGD-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.KYYSPBFCGD-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.KYYSPBFCGD-label {
    margin-bottom: -15px;
    display: block;
}

.KYYSPBFCGD-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#KYYSPBFCGD-popup {
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

.KYYSPBFCGD-selection {
    margin-bottom: 5px;
}

.KYYSPBFCGD-featuretable {
    margin-top: 10px;
}

.KYYSPBFCGD-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.KYYSPBFCGD-fvalue {
    text-align: left !important;
}
</style>
  <div id="KYYSPBFCGD-content">
        <div id="KYYSPBFCGD-popup" style="display: none;">
        </div>
        <div class="KYYSPBFCGD-row" id="KYYSPBFCGD-row1" style="height:67vh; min-height:100px;">
            <div id="KYYSPBFCGD-text-wrapper" class="KYYSPBFCGD-col" style="width:70%;">
                <div class="KYYSPBFCGD-hdr" id="KYYSPBFCGD-dochdr"></div>
                <div id="KYYSPBFCGD-text">
                </div>
            </div>
            <div id="KYYSPBFCGD-chooser" class="KYYSPBFCGD-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="KYYSPBFCGD-row" id="KYYSPBFCGD-row2" style="height:30vh; min-height: 100px;">
            <div id="KYYSPBFCGD-details" class="KYYSPBFCGD-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.11/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="KYYSPBFCGD-data">
    {"annotation_sets": {"": {"name": "detached-from:", "annotations": [{"type": "SomeType", "start": 0, "end": 4, "id": 0, "features": {"annfeature1": 11, "annfeature2": 2, "annfeature3": 3}}, {"type": "SomeType", "start": 5, "end": 7, "id": 1, "features": {}}, {"type": "SomeType", "start": 8, "end": 12, "id": 2, "features": {}}], "next_annid": 0}}, "text": "This is some text", "features": {"feature1": "some value"}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("KYYSPBFCGD-");
    </script>
  </div>

</div></div>



```python

```
