# Web Service Client Annotators

Web service client annotators are annotators which use a web service to annotate documents: for each document that gets processed, data is sent to a HTTP endpoint, processed there and information is sent back that is then used to annotate the document. 

Currently two client annotators are implemented:

* GateCloudAnnotator: this annotator connects to one of the many services on the GATE Cloud platform (https://cloud.gate.ac.uk/). Services include named entity recognition for tweets or standard texts in several  languages, entity disambiguation and linking to Wikipedia or MeSH or Snomed. NOTE: some services require input that is not just plain text, at the moment only those services are supported which can annotate plain text
* TagMe: this annotator connects to the TagMe mention disambiguation and linking service (https://sobigdata.d4science.org/group/tagme/tagme) to either perform the task "tag" (disambiguation and linking of mentions) or "spot" finding mentions only. 



```python
from gatenlp import Document
from gatenlp.processing.client import GateCloudAnnotator


```

Lets try annotating a document with the English Named Entity Recognizer on GATE
cloud (https://cloud.gate.ac.uk/shopfront/displayItem/annie-named-entity-recognizer). 

The information page for that service shows that the following annotation types can be requested of which the first 5 are requested by default if no alternate list is specified:

* Address  (included by default)
* Date (included by default)
* Location (included by default)
* Organization (included by default)
* Person (included by default)
* Money 
* Percent 
* Token 
* SpaceToken 
* Sentence

We create a GateCloudAnnotator an specify the full list of all supported annotation types. We also specify the URL of the service endpoint as provided on the info page and specify that the annotations should be put into the annotation set "ANNIE". Note that a limited number of documents can be annotated for free and without authentication, so we do not need to specify the `api_key` and `api_password` parameters. 


```python
annotator = GateCloudAnnotator(
    url="https://cloud-api.gate.ac.uk/process-document/annie-named-entity-recognizer", 
    out_annset="ANNIE", 
    ann_types=":Address,:Date,:Location,:Organization,:Person,:Money,:Percent,:Token,:SpaceToken,:Sentence"
)
```


```python
# an example document to annotate
doc = Document("Barack Obama visited 💩💩 Microsoft in New York last May.")
```


```python
# Run the annotator and show the annotated document
doc = annotator(doc)
doc
```




<div><style>#IENDGERLUM-wrapper { color: black !important; }</style>
<div id="IENDGERLUM-wrapper">

<div>
<style>
#IENDGERLUM-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.IENDGERLUM-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.IENDGERLUM-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.IENDGERLUM-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.IENDGERLUM-label {
    margin-bottom: -15px;
    display: block;
}

.IENDGERLUM-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#IENDGERLUM-popup {
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

.IENDGERLUM-selection {
    margin-bottom: 5px;
}

.IENDGERLUM-featuretable {
    margin-top: 10px;
}

.IENDGERLUM-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.IENDGERLUM-fvalue {
    text-align: left !important;
}
</style>
  <div id="IENDGERLUM-content">
        <div id="IENDGERLUM-popup" style="display: none;">
        </div>
        <div class="IENDGERLUM-row" id="IENDGERLUM-row1" style="height:67vh; min-height:100px;">
            <div id="IENDGERLUM-text-wrapper" class="IENDGERLUM-col" style="width:70%;">
                <div class="IENDGERLUM-hdr" id="IENDGERLUM-dochdr"></div>
                <div id="IENDGERLUM-text">
                </div>
            </div>
            <div id="IENDGERLUM-chooser" class="IENDGERLUM-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="IENDGERLUM-row" id="IENDGERLUM-row2" style="height:30vh; min-height: 100px;">
            <div id="IENDGERLUM-details" class="IENDGERLUM-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.11/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="IENDGERLUM-data">
    {"annotation_sets": {"ANNIE": {"name": "detached-from:ANNIE", "annotations": [{"type": "Date", "start": 48, "end": 56, "id": 0, "features": {"rule": "ModifierNamedDate", "ruleFinal": "DateOnlyFinal", "kind": "date"}}, {"type": "Location", "start": 39, "end": 47, "id": 1, "features": {"kind": "locName", "rule": "InLoc1", "locType": "city", "ruleFinal": "LocFinal"}}, {"type": "Organization", "start": 26, "end": 35, "id": 2, "features": {"orgType": "company", "rule": "GazOrganization", "ruleFinal": "OrgFinal"}}, {"type": "Person", "start": 0, "end": 12, "id": 3, "features": {"firstName": "Barack", "surname": "Obama", "kind": "fullName", "rule": "GazPerson", "gender": "male", "ruleFinal": "PersonFinal"}}, {"type": "Token", "start": 0, "end": 6, "id": 4, "features": {"string": "Barack", "length": "6", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 7, "end": 12, "id": 5, "features": {"string": "Obama", "length": "5", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 13, "end": 20, "id": 6, "features": {"string": "visited", "length": "7", "orth": "lowercase", "kind": "word", "category": "VBD"}}, {"type": "Token", "start": 21, "end": 23, "id": 7, "features": {"string": "\ud83d\udca9", "length": "2", "kind": "symbol", "category": "NN"}}, {"type": "Token", "start": 23, "end": 25, "id": 8, "features": {"string": "\ud83d\udca9", "length": "2", "kind": "symbol", "category": "NN"}}, {"type": "Token", "start": 26, "end": 35, "id": 9, "features": {"string": "Microsoft", "length": "9", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 36, "end": 38, "id": 10, "features": {"string": "in", "length": "2", "orth": "lowercase", "kind": "word", "category": "IN"}}, {"type": "Token", "start": 39, "end": 42, "id": 11, "features": {"string": "New", "length": "3", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 43, "end": 47, "id": 12, "features": {"string": "York", "length": "4", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 48, "end": 52, "id": 13, "features": {"string": "last", "length": "4", "orth": "lowercase", "kind": "word", "category": "JJ"}}, {"type": "Token", "start": 53, "end": 56, "id": 14, "features": {"string": "May", "length": "3", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 56, "end": 57, "id": 15, "features": {"string": ".", "length": "1", "kind": "punctuation", "category": "."}}, {"type": "SpaceToken", "start": 6, "end": 7, "id": 16, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 12, "end": 13, "id": 17, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 20, "end": 21, "id": 18, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 25, "end": 26, "id": 19, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 35, "end": 36, "id": 20, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 38, "end": 39, "id": 21, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 42, "end": 43, "id": 22, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 47, "end": 48, "id": 23, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 52, "end": 53, "id": 24, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "Sentence", "start": 0, "end": 57, "id": 25, "features": {}}], "next_annid": 26}}, "text": "Barack Obama visited \ud83d\udca9\ud83d\udca9 Microsoft in New York last May.", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("IENDGERLUM-");
    </script>
  </div>

</div></div>


