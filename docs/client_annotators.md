# Web Service Client Annotators

Web service client annotators are annotators which use a web service to annotate documents: for each document that gets processed, data is sent to a HTTP endpoint, processed there and information is sent back that is then used to annotate the document. 

Currently two client annotators are implemented:

* GateCloudAnnotator: this annotator connects to one of the many services on the GATE Cloud platform (https://cloud.gate.ac.uk/). Services include named entity recognition for tweets or standard texts in several  languages, entity disambiguation and linking to Wikipedia or MeSH or Snomed. NOTE: some services require input that is not just plain text, at the moment only those services are supported which can annotate plain text
* TagMeAnnotator: this annotator connects to the TagMe mention disambiguation and linking service (https://sobigdata.d4science.org/group/tagme/tagme) to either perform the task "tag" (disambiguation and linking of mentions) or "spot" finding mentions only. 
* TextRazorTextAnnotator: this annotator connects to the TextRazor API endpoint (see https://www.textrazor.com/) to annotate the text of the document
* ElgTextAnnotator: this annotator connects to one of the public endpoints from the European Language Grid project (see https://live.european-language-grid.eu) 



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
doc = Document("Barack Obama visited Microsoft in New York last May.")
```


```python
# Run the annotator and show the annotated document
doc = annotator(doc)
doc
```




<div><style>#MOUFKYLXSS-wrapper { color: black !important; }</style>
<div id="MOUFKYLXSS-wrapper">

<div>
<style>
#MOUFKYLXSS-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.MOUFKYLXSS-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.MOUFKYLXSS-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.MOUFKYLXSS-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.MOUFKYLXSS-label {
    margin-bottom: -15px;
    display: block;
}

.MOUFKYLXSS-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#MOUFKYLXSS-popup {
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

.MOUFKYLXSS-selection {
    margin-bottom: 5px;
}

.MOUFKYLXSS-featuretable {
    margin-top: 10px;
}

.MOUFKYLXSS-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.MOUFKYLXSS-fvalue {
    text-align: left !important;
}
</style>
  <div id="MOUFKYLXSS-content">
        <div id="MOUFKYLXSS-popup" style="display: none;">
        </div>
        <div class="MOUFKYLXSS-row" id="MOUFKYLXSS-row1" style="height:67vh; min-height:100px;">
            <div id="MOUFKYLXSS-text-wrapper" class="MOUFKYLXSS-col" style="width:70%;">
                <div class="MOUFKYLXSS-hdr" id="MOUFKYLXSS-dochdr"></div>
                <div id="MOUFKYLXSS-text">
                </div>
            </div>
            <div id="MOUFKYLXSS-chooser" class="MOUFKYLXSS-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="MOUFKYLXSS-row" id="MOUFKYLXSS-row2" style="height:30vh; min-height: 100px;">
            <div id="MOUFKYLXSS-details" class="MOUFKYLXSS-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.11/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="MOUFKYLXSS-data">
    {"annotation_sets": {"ANNIE": {"name": "detached-from:ANNIE", "annotations": [{"type": "Date", "start": 43, "end": 51, "id": 0, "features": {"rule": "ModifierNamedDate", "ruleFinal": "DateOnlyFinal", "kind": "date"}}, {"type": "Location", "start": 34, "end": 42, "id": 1, "features": {"kind": "locName", "rule": "InLoc1", "locType": "city", "ruleFinal": "LocFinal"}}, {"type": "Organization", "start": 21, "end": 30, "id": 2, "features": {"orgType": "company", "rule": "GazOrganization", "ruleFinal": "OrgFinal"}}, {"type": "Person", "start": 0, "end": 12, "id": 3, "features": {"firstName": "Barack", "surname": "Obama", "kind": "fullName", "rule": "GazPerson", "gender": "male", "ruleFinal": "PersonFinal"}}, {"type": "Token", "start": 0, "end": 6, "id": 4, "features": {"string": "Barack", "length": "6", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 7, "end": 12, "id": 5, "features": {"string": "Obama", "length": "5", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 13, "end": 20, "id": 6, "features": {"string": "visited", "length": "7", "orth": "lowercase", "kind": "word", "category": "VBD"}}, {"type": "Token", "start": 21, "end": 30, "id": 7, "features": {"string": "Microsoft", "length": "9", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 31, "end": 33, "id": 8, "features": {"string": "in", "length": "2", "orth": "lowercase", "kind": "word", "category": "IN"}}, {"type": "Token", "start": 34, "end": 37, "id": 9, "features": {"string": "New", "length": "3", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 38, "end": 42, "id": 10, "features": {"string": "York", "length": "4", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 43, "end": 47, "id": 11, "features": {"string": "last", "length": "4", "orth": "lowercase", "kind": "word", "category": "JJ"}}, {"type": "Token", "start": 48, "end": 51, "id": 12, "features": {"string": "May", "length": "3", "orth": "upperInitial", "kind": "word", "category": "NNP"}}, {"type": "Token", "start": 51, "end": 52, "id": 13, "features": {"string": ".", "length": "1", "kind": "punctuation", "category": "."}}, {"type": "SpaceToken", "start": 6, "end": 7, "id": 14, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 12, "end": 13, "id": 15, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 20, "end": 21, "id": 16, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 30, "end": 31, "id": 17, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 33, "end": 34, "id": 18, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 37, "end": 38, "id": 19, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 42, "end": 43, "id": 20, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "SpaceToken", "start": 47, "end": 48, "id": 21, "features": {"string": " ", "length": "1", "kind": "space"}}, {"type": "Sentence", "start": 0, "end": 52, "id": 22, "features": {}}], "next_annid": 23}}, "text": "Barack Obama visited Microsoft in New York last May.", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("MOUFKYLXSS-");
    </script>
  </div>

</div></div>


