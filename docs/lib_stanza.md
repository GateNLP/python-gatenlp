# Stanza pipeline

If `gatenlp` has been installed with the stanza extra (`pip install gatenlp[stanza]` or `pip install gatenlp[all]`) you can run a Stanford Stanza pipeline on a document and get the result as `gatenlp` annotations. 




```python
from gatenlp import Document
from gatenlp.lib_stanza import AnnStanza
import stanza


```


```python
# In order to use the English pipeline with stanza, the model has to get downloaded first
stanza.download('en')
```

    Downloading https://raw.githubusercontent.com/stanfordnlp/stanza-resources/master/resources_1.1.0.json: 122kB [00:00, 6.98MB/s]                    
    INFO:stanza:Downloading default packages for language: en (English)...
    INFO:stanza:File exists: /home/johann/stanza_resources/en/default.zip.
    INFO:stanza:Finished downloading models and saved to /home/johann/stanza_resources.



```python
doc = Document.load("https://gatenlp.github.io/python-gatenlp/testdocument2.txt")
doc
```




<div><style>#LEHDAEOERM-wrapper { color: black !important; }</style>
<div id="LEHDAEOERM-wrapper">

<div>
<style>
#LEHDAEOERM-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.LEHDAEOERM-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.LEHDAEOERM-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.LEHDAEOERM-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.LEHDAEOERM-label {
    margin-bottom: -15px;
    display: block;
}

.LEHDAEOERM-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#LEHDAEOERM-popup {
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

.LEHDAEOERM-selection {
    margin-bottom: 5px;
}

.LEHDAEOERM-featuretable {
    margin-top: 10px;
}

.LEHDAEOERM-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.LEHDAEOERM-fvalue {
    text-align: left !important;
}
</style>
  <div id="LEHDAEOERM-content">
        <div id="LEHDAEOERM-popup" style="display: none;">
        </div>
        <div class="LEHDAEOERM-row" id="LEHDAEOERM-row1" style="height:67vh; min-height:100px;">
            <div id="LEHDAEOERM-text-wrapper" class="LEHDAEOERM-col" style="width:70%;">
                <div class="LEHDAEOERM-hdr" id="LEHDAEOERM-dochdr"></div>
                <div id="LEHDAEOERM-text">
                </div>
            </div>
            <div id="LEHDAEOERM-chooser" class="LEHDAEOERM-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="LEHDAEOERM-row" id="LEHDAEOERM-row2" style="height:30vh; min-height: 100px;">
            <div id="LEHDAEOERM-details" class="LEHDAEOERM-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.9/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="LEHDAEOERM-data">
    {"annotation_sets": {}, "text": "This is just a sample document for experimenting with gatenlp. \nIt mentions a few named entities like the persons Barack Obama, \nAlbert Einstein and Wolfgang Amadeus Mozart and the geographical \nlocations and countries America, United States of America, \nHungary, the Atlantic Ocean, and Helskinki. \n\nIt also contains mentions of various numbers and amounts like \n12 degrees, 12.83$, 25 km/h or fortytwo kilos and mentions\norganizations and companies like the UNO, Microsoft, Apple, which\nhas an apple as it's logo, or Google. \n\n\n", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("LEHDAEOERM-");
    </script>
  </div>

</div></div>



## Annotating the document using Stanza

In order to annotate one or more documents using Stanza, first create a AnnStanza annotator object
and the run the document(s) through this annotator:


```python
stanza_annotator = AnnStanza(lang="en")
```

    INFO:stanza:Loading these models for language: en (English):
    =========================
    | Processor | Package   |
    -------------------------
    | tokenize  | ewt       |
    | pos       | ewt       |
    | lemma     | ewt       |
    | depparse  | ewt       |
    | sentiment | sstplus   |
    | ner       | ontonotes |
    =========================
    
    INFO:stanza:Use device: cpu
    INFO:stanza:Loading: tokenize
    INFO:stanza:Loading: pos
    INFO:stanza:Loading: lemma
    INFO:stanza:Loading: depparse
    INFO:stanza:Loading: sentiment
    INFO:stanza:Loading: ner
    INFO:stanza:Done loading processors!



```python
doc = stanza_annotator(doc)
doc
```




<div><style>#QIUNTDRRJE-wrapper { color: black !important; }</style>
<div id="QIUNTDRRJE-wrapper">

<div>
<style>
#QIUNTDRRJE-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.QIUNTDRRJE-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.QIUNTDRRJE-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.QIUNTDRRJE-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.QIUNTDRRJE-label {
    margin-bottom: -15px;
    display: block;
}

.QIUNTDRRJE-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#QIUNTDRRJE-popup {
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

.QIUNTDRRJE-selection {
    margin-bottom: 5px;
}

.QIUNTDRRJE-featuretable {
    margin-top: 10px;
}

.QIUNTDRRJE-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.QIUNTDRRJE-fvalue {
    text-align: left !important;
}
</style>
  <div id="QIUNTDRRJE-content">
        <div id="QIUNTDRRJE-popup" style="display: none;">
        </div>
        <div class="QIUNTDRRJE-row" id="QIUNTDRRJE-row1" style="height:67vh; min-height:100px;">
            <div id="QIUNTDRRJE-text-wrapper" class="QIUNTDRRJE-col" style="width:70%;">
                <div class="QIUNTDRRJE-hdr" id="QIUNTDRRJE-dochdr"></div>
                <div id="QIUNTDRRJE-text">
                </div>
            </div>
            <div id="QIUNTDRRJE-chooser" class="QIUNTDRRJE-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="QIUNTDRRJE-row" id="QIUNTDRRJE-row2" style="height:30vh; min-height: 100px;">
            <div id="QIUNTDRRJE-details" class="QIUNTDRRJE-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.9/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="QIUNTDRRJE-data">
    {"annotation_sets": {"": {"name": "detached-from:", "annotations": [{"type": "Token", "start": 0, "end": 4, "id": 0, "features": {"id": 1, "text": "This", "lemma": "this", "upos": "PRON", "xpos": "DT", "head": 5, "deprel": "nsubj", "ner": "O", "Number": "Sing", "PronType": "Dem"}}, {"type": "Token", "start": 5, "end": 7, "id": 1, "features": {"id": 2, "text": "is", "lemma": "be", "upos": "AUX", "xpos": "VBZ", "head": 5, "deprel": "cop", "ner": "O", "Mood": "Ind", "Number": "Sing", "Person": "3", "Tense": "Pres", "VerbForm": "Fin"}}, {"type": "Token", "start": 8, "end": 12, "id": 2, "features": {"id": 3, "text": "just", "lemma": "just", "upos": "ADV", "xpos": "RB", "head": 5, "deprel": "advmod", "ner": "O"}}, {"type": "Token", "start": 13, "end": 14, "id": 3, "features": {"id": 4, "text": "a", "lemma": "a", "upos": "DET", "xpos": "DT", "head": 5, "deprel": "det", "ner": "O", "Definite": "Ind", "PronType": "Art"}}, {"type": "Token", "start": 15, "end": 21, "id": 4, "features": {"id": 5, "text": "sample", "lemma": "sample", "upos": "NOUN", "xpos": "NN", "head": 5, "deprel": "compound", "ner": "O", "Number": "Sing"}}, {"type": "Token", "start": 22, "end": 30, "id": 5, "features": {"id": 6, "text": "document", "lemma": "document", "upos": "NOUN", "xpos": "NN", "head": 11, "deprel": "root", "ner": "O", "Number": "Sing"}}, {"type": "Token", "start": 31, "end": 34, "id": 6, "features": {"id": 7, "text": "for", "lemma": "for", "upos": "SCONJ", "xpos": "IN", "head": 7, "deprel": "mark", "ner": "O"}}, {"type": "Token", "start": 35, "end": 48, "id": 7, "features": {"id": 8, "text": "experimenting", "lemma": "experiment", "upos": "VERB", "xpos": "VBG", "head": 5, "deprel": "acl", "ner": "O", "VerbForm": "Ger"}}, {"type": "Token", "start": 49, "end": 53, "id": 8, "features": {"id": 9, "text": "with", "lemma": "with", "upos": "ADP", "xpos": "IN", "head": 9, "deprel": "case", "ner": "O"}}, {"type": "Token", "start": 54, "end": 61, "id": 9, "features": {"id": 10, "text": "gatenlp", "lemma": "gatenlp", "upos": "NOUN", "xpos": "NN", "head": 7, "deprel": "obl", "ner": "O", "Number": "Sing"}}, {"type": "Token", "start": 61, "end": 62, "id": 10, "features": {"id": 11, "text": ".", "lemma": ".", "upos": "PUNCT", "xpos": ".", "head": 5, "deprel": "punct", "ner": "O"}}, {"type": "Sentence", "start": 0, "end": 62, "id": 11, "features": {}}, {"type": "Token", "start": 64, "end": 66, "id": 12, "features": {"id": 1, "text": "It", "lemma": "it", "upos": "PRON", "xpos": "PRP", "head": 13, "deprel": "nsubj", "ner": "O", "Case": "Nom", "Gender": "Neut", "Number": "Sing", "Person": "3", "PronType": "Prs"}}, {"type": "Token", "start": 67, "end": 75, "id": 13, "features": {"id": 2, "text": "mentions", "lemma": "mention", "upos": "VERB", "xpos": "VBZ", "head": 52, "deprel": "root", "ner": "O", "Mood": "Ind", "Number": "Sing", "Person": "3", "Tense": "Pres", "VerbForm": "Fin"}}, {"type": "Token", "start": 76, "end": 77, "id": 14, "features": {"id": 3, "text": "a", "lemma": "a", "upos": "DET", "xpos": "DT", "head": 17, "deprel": "det", "ner": "O", "Definite": "Ind", "PronType": "Art"}}, {"type": "Token", "start": 78, "end": 81, "id": 15, "features": {"id": 4, "text": "few", "lemma": "few", "upos": "ADJ", "xpos": "JJ", "head": 17, "deprel": "amod", "ner": "O", "Degree": "Pos"}}, {"type": "Token", "start": 82, "end": 87, "id": 16, "features": {"id": 5, "text": "named", "lemma": "name", "upos": "VERB", "xpos": "VBN", "head": 17, "deprel": "amod", "ner": "O", "Tense": "Past", "VerbForm": "Part"}}, {"type": "Token", "start": 88, "end": 96, "id": 17, "features": {"id": 6, "text": "entities", "lemma": "entity", "upos": "NOUN", "xpos": "NNS", "head": 13, "deprel": "obj", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 97, "end": 101, "id": 18, "features": {"id": 7, "text": "like", "lemma": "like", "upos": "ADP", "xpos": "IN", "head": 20, "deprel": "case", "ner": "O"}}, {"type": "Token", "start": 102, "end": 105, "id": 19, "features": {"id": 8, "text": "the", "lemma": "the", "upos": "DET", "xpos": "DT", "head": 20, "deprel": "det", "ner": "O", "Definite": "Def", "PronType": "Art"}}, {"type": "Token", "start": 106, "end": 113, "id": 20, "features": {"id": 9, "text": "persons", "lemma": "person", "upos": "NOUN", "xpos": "NNS", "head": 17, "deprel": "nmod", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 114, "end": 120, "id": 21, "features": {"id": 10, "text": "Barack", "lemma": "Barack", "upos": "PROPN", "xpos": "NNP", "head": 20, "deprel": "appos", "ner": "B-PERSON", "Number": "Sing"}}, {"type": "Token", "start": 121, "end": 126, "id": 22, "features": {"id": 11, "text": "Obama", "lemma": "Obama", "upos": "PROPN", "xpos": "NNP", "head": 21, "deprel": "flat", "ner": "E-PERSON", "Number": "Sing"}}, {"type": "Token", "start": 126, "end": 127, "id": 23, "features": {"id": 12, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 24, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 129, "end": 135, "id": 24, "features": {"id": 13, "text": "Albert", "lemma": "Albert", "upos": "PROPN", "xpos": "NNP", "head": 21, "deprel": "conj", "ner": "B-PERSON", "Number": "Sing"}}, {"type": "Token", "start": 136, "end": 144, "id": 25, "features": {"id": 14, "text": "Einstein", "lemma": "Einstein", "upos": "PROPN", "xpos": "NNP", "head": 24, "deprel": "flat", "ner": "E-PERSON", "Number": "Sing"}}, {"type": "Token", "start": 145, "end": 148, "id": 26, "features": {"id": 15, "text": "and", "lemma": "and", "upos": "CCONJ", "xpos": "CC", "head": 27, "deprel": "cc", "ner": "O"}}, {"type": "Token", "start": 149, "end": 157, "id": 27, "features": {"id": 16, "text": "Wolfgang", "lemma": "Wolfgang", "upos": "PROPN", "xpos": "NNP", "head": 20, "deprel": "conj", "ner": "B-PERSON", "Number": "Sing"}}, {"type": "Token", "start": 158, "end": 165, "id": 28, "features": {"id": 17, "text": "Amadeus", "lemma": "Amadeus", "upos": "PROPN", "xpos": "NNP", "head": 27, "deprel": "flat", "ner": "I-PERSON", "Number": "Sing"}}, {"type": "Token", "start": 166, "end": 172, "id": 29, "features": {"id": 18, "text": "Mozart", "lemma": "Mozart", "upos": "PROPN", "xpos": "NNP", "head": 27, "deprel": "flat", "ner": "E-PERSON", "Number": "Sing"}}, {"type": "Token", "start": 173, "end": 176, "id": 30, "features": {"id": 19, "text": "and", "lemma": "and", "upos": "CCONJ", "xpos": "CC", "head": 33, "deprel": "cc", "ner": "O"}}, {"type": "Token", "start": 177, "end": 180, "id": 31, "features": {"id": 20, "text": "the", "lemma": "the", "upos": "DET", "xpos": "DT", "head": 33, "deprel": "det", "ner": "O", "Definite": "Def", "PronType": "Art"}}, {"type": "Token", "start": 181, "end": 193, "id": 32, "features": {"id": 21, "text": "geographical", "lemma": "geographical", "upos": "ADJ", "xpos": "JJ", "head": 33, "deprel": "amod", "ner": "O", "Degree": "Pos"}}, {"type": "Token", "start": 195, "end": 204, "id": 33, "features": {"id": 22, "text": "locations", "lemma": "location", "upos": "NOUN", "xpos": "NNS", "head": 20, "deprel": "conj", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 205, "end": 208, "id": 34, "features": {"id": 23, "text": "and", "lemma": "and", "upos": "CCONJ", "xpos": "CC", "head": 36, "deprel": "cc", "ner": "O"}}, {"type": "Token", "start": 209, "end": 218, "id": 35, "features": {"id": 24, "text": "countries", "lemma": "country", "upos": "NOUN", "xpos": "NNS", "head": 36, "deprel": "compound", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 219, "end": 226, "id": 36, "features": {"id": 25, "text": "America", "lemma": "America", "upos": "PROPN", "xpos": "NNP", "head": 20, "deprel": "conj", "ner": "S-GPE", "Number": "Sing"}}, {"type": "Token", "start": 226, "end": 227, "id": 37, "features": {"id": 26, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 39, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 228, "end": 234, "id": 38, "features": {"id": 27, "text": "United", "lemma": "United", "upos": "PROPN", "xpos": "NNP", "head": 39, "deprel": "compound", "ner": "B-GPE", "Number": "Sing"}}, {"type": "Token", "start": 235, "end": 241, "id": 39, "features": {"id": 28, "text": "States", "lemma": "States", "upos": "PROPN", "xpos": "NNP", "head": 20, "deprel": "conj", "ner": "I-GPE", "Number": "Sing"}}, {"type": "Token", "start": 242, "end": 244, "id": 40, "features": {"id": 29, "text": "of", "lemma": "of", "upos": "ADP", "xpos": "IN", "head": 41, "deprel": "case", "ner": "I-GPE"}}, {"type": "Token", "start": 245, "end": 252, "id": 41, "features": {"id": 30, "text": "America", "lemma": "America", "upos": "PROPN", "xpos": "NNP", "head": 39, "deprel": "nmod", "ner": "E-GPE", "Number": "Sing"}}, {"type": "Token", "start": 252, "end": 253, "id": 42, "features": {"id": 31, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 43, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 255, "end": 262, "id": 43, "features": {"id": 32, "text": "Hungary", "lemma": "Hungary", "upos": "PROPN", "xpos": "NNP", "head": 41, "deprel": "conj", "ner": "S-GPE", "Number": "Sing"}}, {"type": "Token", "start": 262, "end": 263, "id": 44, "features": {"id": 33, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 47, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 264, "end": 267, "id": 45, "features": {"id": 34, "text": "the", "lemma": "the", "upos": "DET", "xpos": "DT", "head": 47, "deprel": "det", "ner": "B-LOC", "Definite": "Def", "PronType": "Art"}}, {"type": "Token", "start": 268, "end": 276, "id": 46, "features": {"id": 35, "text": "Atlantic", "lemma": "Atlantic", "upos": "PROPN", "xpos": "NNP", "head": 47, "deprel": "compound", "ner": "I-LOC", "Number": "Sing"}}, {"type": "Token", "start": 277, "end": 282, "id": 47, "features": {"id": 36, "text": "Ocean", "lemma": "Ocean", "upos": "PROPN", "xpos": "NNP", "head": 20, "deprel": "conj", "ner": "E-LOC", "Number": "Sing"}}, {"type": "Token", "start": 282, "end": 283, "id": 48, "features": {"id": 37, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 50, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 284, "end": 287, "id": 49, "features": {"id": 38, "text": "and", "lemma": "and", "upos": "CCONJ", "xpos": "CC", "head": 50, "deprel": "cc", "ner": "O"}}, {"type": "Token", "start": 288, "end": 297, "id": 50, "features": {"id": 39, "text": "Helskinki", "lemma": "Helskinki", "upos": "PROPN", "xpos": "NNP", "head": 20, "deprel": "conj", "ner": "S-ORG", "Number": "Sing"}}, {"type": "Token", "start": 297, "end": 298, "id": 51, "features": {"id": 40, "text": ".", "lemma": ".", "upos": "PUNCT", "xpos": ".", "head": 13, "deprel": "punct", "ner": "O"}}, {"type": "Sentence", "start": 64, "end": 298, "id": 52, "features": {}}, {"type": "Token", "start": 301, "end": 303, "id": 53, "features": {"id": 1, "text": "It", "lemma": "it", "upos": "PRON", "xpos": "PRP", "head": 55, "deprel": "nsubj", "ner": "O", "Case": "Nom", "Gender": "Neut", "Number": "Sing", "Person": "3", "PronType": "Prs"}}, {"type": "Token", "start": 304, "end": 308, "id": 54, "features": {"id": 2, "text": "also", "lemma": "also", "upos": "ADV", "xpos": "RB", "head": 55, "deprel": "advmod", "ner": "O"}}, {"type": "Token", "start": 309, "end": 317, "id": 55, "features": {"id": 3, "text": "contains", "lemma": "contain", "upos": "VERB", "xpos": "VBZ", "head": 101, "deprel": "root", "ner": "O", "Mood": "Ind", "Number": "Sing", "Person": "3", "Tense": "Pres", "VerbForm": "Fin"}}, {"type": "Token", "start": 318, "end": 326, "id": 56, "features": {"id": 4, "text": "mentions", "lemma": "mention", "upos": "NOUN", "xpos": "NNS", "head": 55, "deprel": "obj", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 327, "end": 329, "id": 57, "features": {"id": 5, "text": "of", "lemma": "of", "upos": "ADP", "xpos": "IN", "head": 59, "deprel": "case", "ner": "O"}}, {"type": "Token", "start": 330, "end": 337, "id": 58, "features": {"id": 6, "text": "various", "lemma": "various", "upos": "ADJ", "xpos": "JJ", "head": 59, "deprel": "amod", "ner": "O", "Degree": "Pos"}}, {"type": "Token", "start": 338, "end": 345, "id": 59, "features": {"id": 7, "text": "numbers", "lemma": "number", "upos": "NOUN", "xpos": "NNS", "head": 56, "deprel": "nmod", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 346, "end": 349, "id": 60, "features": {"id": 8, "text": "and", "lemma": "and", "upos": "CCONJ", "xpos": "CC", "head": 61, "deprel": "cc", "ner": "O"}}, {"type": "Token", "start": 350, "end": 357, "id": 61, "features": {"id": 9, "text": "amounts", "lemma": "amount", "upos": "NOUN", "xpos": "NNS", "head": 59, "deprel": "conj", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 358, "end": 362, "id": 62, "features": {"id": 10, "text": "like", "lemma": "like", "upos": "ADP", "xpos": "IN", "head": 64, "deprel": "case", "ner": "O"}}, {"type": "Token", "start": 364, "end": 366, "id": 63, "features": {"id": 11, "text": "12", "lemma": "12", "upos": "NUM", "xpos": "CD", "head": 64, "deprel": "nummod", "ner": "B-QUANTITY", "NumType": "Card"}}, {"type": "Token", "start": 367, "end": 374, "id": 64, "features": {"id": 12, "text": "degrees", "lemma": "degree", "upos": "NOUN", "xpos": "NNS", "head": 59, "deprel": "nmod", "ner": "E-QUANTITY", "Number": "Plur"}}, {"type": "Token", "start": 374, "end": 375, "id": 65, "features": {"id": 13, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 67, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 376, "end": 381, "id": 66, "features": {"id": 14, "text": "12.83", "lemma": "12.83", "upos": "NUM", "xpos": "CD", "head": 67, "deprel": "nummod", "ner": "O", "NumType": "Card"}}, {"type": "Token", "start": 381, "end": 382, "id": 67, "features": {"id": 15, "text": "$", "lemma": "$", "upos": "SYM", "xpos": "$", "head": 59, "deprel": "conj", "ner": "O"}}, {"type": "Token", "start": 382, "end": 383, "id": 68, "features": {"id": 16, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 70, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 384, "end": 386, "id": 69, "features": {"id": 17, "text": "25", "lemma": "25", "upos": "NUM", "xpos": "CD", "head": 70, "deprel": "nummod", "ner": "B-QUANTITY", "NumType": "Card"}}, {"type": "Token", "start": 387, "end": 389, "id": 70, "features": {"id": 18, "text": "km", "lemma": "km", "upos": "NOUN", "xpos": "NNS", "head": 67, "deprel": "conj", "ner": "I-QUANTITY", "Number": "Plur"}}, {"type": "Token", "start": 389, "end": 390, "id": 71, "features": {"id": 19, "text": "/", "lemma": "/", "upos": "PUNCT", "xpos": ",", "head": 72, "deprel": "punct", "ner": "I-QUANTITY"}}, {"type": "Token", "start": 390, "end": 391, "id": 72, "features": {"id": 20, "text": "h", "lemma": "h", "upos": "NOUN", "xpos": "NN", "head": 67, "deprel": "conj", "ner": "E-QUANTITY", "Number": "Sing"}}, {"type": "Token", "start": 392, "end": 394, "id": 73, "features": {"id": 21, "text": "or", "lemma": "or", "upos": "CCONJ", "xpos": "CC", "head": 75, "deprel": "cc", "ner": "O"}}, {"type": "Token", "start": 395, "end": 403, "id": 74, "features": {"id": 22, "text": "fortytwo", "lemma": "fortytwo", "upos": "ADJ", "xpos": "JJ", "head": 75, "deprel": "amod", "ner": "B-QUANTITY", "Degree": "Pos"}}, {"type": "Token", "start": 404, "end": 409, "id": 75, "features": {"id": 23, "text": "kilos", "lemma": "kilo", "upos": "NOUN", "xpos": "NNS", "head": 67, "deprel": "conj", "ner": "E-QUANTITY", "Number": "Plur"}}, {"type": "Token", "start": 410, "end": 413, "id": 76, "features": {"id": 24, "text": "and", "lemma": "and", "upos": "CCONJ", "xpos": "CC", "head": 78, "deprel": "cc", "ner": "O"}}, {"type": "Token", "start": 414, "end": 422, "id": 77, "features": {"id": 25, "text": "mentions", "lemma": "mention", "upos": "NOUN", "xpos": "NNS", "head": 78, "deprel": "compound", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 423, "end": 436, "id": 78, "features": {"id": 26, "text": "organizations", "lemma": "organization", "upos": "NOUN", "xpos": "NNS", "head": 59, "deprel": "conj", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 437, "end": 440, "id": 79, "features": {"id": 27, "text": "and", "lemma": "and", "upos": "CCONJ", "xpos": "CC", "head": 80, "deprel": "cc", "ner": "O"}}, {"type": "Token", "start": 441, "end": 450, "id": 80, "features": {"id": 28, "text": "companies", "lemma": "company", "upos": "NOUN", "xpos": "NNS", "head": 59, "deprel": "conj", "ner": "O", "Number": "Plur"}}, {"type": "Token", "start": 451, "end": 455, "id": 81, "features": {"id": 29, "text": "like", "lemma": "like", "upos": "ADP", "xpos": "IN", "head": 83, "deprel": "case", "ner": "O"}}, {"type": "Token", "start": 456, "end": 459, "id": 82, "features": {"id": 30, "text": "the", "lemma": "the", "upos": "DET", "xpos": "DT", "head": 83, "deprel": "det", "ner": "O", "Definite": "Def", "PronType": "Art"}}, {"type": "Token", "start": 460, "end": 463, "id": 83, "features": {"id": 31, "text": "UNO", "lemma": "UNO", "upos": "PROPN", "xpos": "NNP", "head": 80, "deprel": "nmod", "ner": "S-ORG", "Number": "Sing"}}, {"type": "Token", "start": 463, "end": 464, "id": 84, "features": {"id": 32, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 83, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 465, "end": 474, "id": 85, "features": {"id": 33, "text": "Microsoft", "lemma": "Microsoft", "upos": "PROPN", "xpos": "NNP", "head": 83, "deprel": "appos", "ner": "S-ORG", "Number": "Sing"}}, {"type": "Token", "start": 474, "end": 475, "id": 86, "features": {"id": 34, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 85, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 476, "end": 481, "id": 87, "features": {"id": 35, "text": "Apple", "lemma": "Apple", "upos": "PROPN", "xpos": "NNP", "head": 83, "deprel": "appos", "ner": "S-ORG", "Number": "Sing"}}, {"type": "Token", "start": 481, "end": 482, "id": 88, "features": {"id": 36, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 83, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 483, "end": 488, "id": 89, "features": {"id": 37, "text": "which", "lemma": "which", "upos": "PRON", "xpos": "WDT", "head": 90, "deprel": "nsubj", "ner": "O", "PronType": "Rel"}}, {"type": "Token", "start": 489, "end": 492, "id": 90, "features": {"id": 38, "text": "has", "lemma": "have", "upos": "VERB", "xpos": "VBZ", "head": 83, "deprel": "acl:relcl", "ner": "O", "Mood": "Ind", "Number": "Sing", "Person": "3", "Tense": "Pres", "VerbForm": "Fin"}}, {"type": "Token", "start": 493, "end": 495, "id": 91, "features": {"id": 39, "text": "an", "lemma": "a", "upos": "DET", "xpos": "DT", "head": 92, "deprel": "det", "ner": "O", "Definite": "Ind", "PronType": "Art"}}, {"type": "Token", "start": 496, "end": 501, "id": 92, "features": {"id": 40, "text": "apple", "lemma": "apple", "upos": "NOUN", "xpos": "NN", "head": 90, "deprel": "obj", "ner": "O", "Number": "Sing"}}, {"type": "Token", "start": 502, "end": 504, "id": 93, "features": {"id": 41, "text": "as", "lemma": "as", "upos": "ADP", "xpos": "IN", "head": 96, "deprel": "mark", "ner": "O"}}, {"type": "Token", "start": 505, "end": 507, "id": 94, "features": {"id": 42, "text": "it", "lemma": "it", "upos": "PRON", "xpos": "PRP", "head": 96, "deprel": "nsubj", "ner": "O", "Case": "Nom", "Gender": "Neut", "Number": "Sing", "Person": "3", "PronType": "Prs"}}, {"type": "Token", "start": 507, "end": 509, "id": 95, "features": {"id": 43, "text": "'s", "lemma": "be", "upos": "AUX", "xpos": "VBZ", "head": 96, "deprel": "cop", "ner": "O", "Mood": "Ind", "Number": "Sing", "Person": "3", "Tense": "Pres", "VerbForm": "Fin"}}, {"type": "Token", "start": 510, "end": 514, "id": 96, "features": {"id": 44, "text": "logo", "lemma": "logo", "upos": "NOUN", "xpos": "NN", "head": 90, "deprel": "advcl", "ner": "O", "Number": "Sing"}}, {"type": "Token", "start": 514, "end": 515, "id": 97, "features": {"id": 45, "text": ",", "lemma": ",", "upos": "PUNCT", "xpos": ",", "head": 99, "deprel": "punct", "ner": "O"}}, {"type": "Token", "start": 516, "end": 518, "id": 98, "features": {"id": 46, "text": "or", "lemma": "or", "upos": "CCONJ", "xpos": "CC", "head": 99, "deprel": "cc", "ner": "O"}}, {"type": "Token", "start": 519, "end": 525, "id": 99, "features": {"id": 47, "text": "Google", "lemma": "Google", "upos": "PROPN", "xpos": "NNP", "head": 96, "deprel": "conj", "ner": "S-ORG", "Number": "Sing"}}, {"type": "Token", "start": 525, "end": 526, "id": 100, "features": {"id": 48, "text": ".", "lemma": ".", "upos": "PUNCT", "xpos": ".", "head": 55, "deprel": "punct", "ner": "O"}}, {"type": "Sentence", "start": 301, "end": 526, "id": 101, "features": {}}, {"type": "PERSON", "start": 114, "end": 126, "id": 102, "features": {}}, {"type": "PERSON", "start": 129, "end": 144, "id": 103, "features": {}}, {"type": "PERSON", "start": 149, "end": 172, "id": 104, "features": {}}, {"type": "GPE", "start": 219, "end": 226, "id": 105, "features": {}}, {"type": "GPE", "start": 228, "end": 252, "id": 106, "features": {}}, {"type": "GPE", "start": 255, "end": 262, "id": 107, "features": {}}, {"type": "LOC", "start": 264, "end": 282, "id": 108, "features": {}}, {"type": "ORG", "start": 288, "end": 297, "id": 109, "features": {}}, {"type": "QUANTITY", "start": 364, "end": 374, "id": 110, "features": {}}, {"type": "QUANTITY", "start": 384, "end": 391, "id": 111, "features": {}}, {"type": "QUANTITY", "start": 395, "end": 409, "id": 112, "features": {}}, {"type": "ORG", "start": 460, "end": 463, "id": 113, "features": {}}, {"type": "ORG", "start": 465, "end": 474, "id": 114, "features": {}}, {"type": "ORG", "start": 476, "end": 481, "id": 115, "features": {}}, {"type": "ORG", "start": 519, "end": 525, "id": 116, "features": {}}], "next_annid": 117}}, "text": "This is just a sample document for experimenting with gatenlp. \nIt mentions a few named entities like the persons Barack Obama, \nAlbert Einstein and Wolfgang Amadeus Mozart and the geographical \nlocations and countries America, United States of America, \nHungary, the Atlantic Ocean, and Helskinki. \n\nIt also contains mentions of various numbers and amounts like \n12 degrees, 12.83$, 25 km/h or fortytwo kilos and mentions\norganizations and companies like the UNO, Microsoft, Apple, which\nhas an apple as it's logo, or Google. \n\n\n", "features": {}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("QIUNTDRRJE-");
    </script>
  </div>

</div></div>




```python

```
