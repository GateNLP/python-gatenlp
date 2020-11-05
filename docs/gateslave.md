# GATE Slave

The GATE Slave is a module that allows to run anything in a Java GATE process from Python and interchange documents between Python and Java.

One possible use of this is to run an existing GATE pipeline on a Python GateNLP document.

This is done by the python module communicating with a Java process over a socket connection. 
Java calls on the Python side are sent over to Java, executed and the result is send back to Python. 

For this to work, GATE and Java have to be installed on the machine that runs the GATE Slave.

The easiest way to run this is by first manually starting the GATE Slave in the Java GATE GUI and then 
connecting to it from the Python side. 

## Manually starting the GATE Slave from GATE

1. Start GATE
2. Load the Python plugin using the CREOLE Plugin Manager
3. Create a new Language Resource: "PythonSlaveLr"

When creating the PyhonSlaveLr, the following initialization parameters can be specified:
* `authToken`: this is used to prevent other processes from connecting to the slave. You can either specify 
  some string here or with `useAuthToken` set to `true` let GATE choose a random one and display it in the 
  message pane after the resource has been created. 
* `host`:  The host name or address to bind to. The default 127.0.0.1 makes the slave only visible on the same
  machine. In order to make it visible on other machines, use the host name or IP address on the network
  or use 0.0.0.0 
* `logActions`: if this is set to true, the actions requested by the Python process are logged to the message pane. 
* `port`: the port number to use. Each slave requires their own port number so if more than one slave is running
  on a machine, they need to use different, unused port numbers. 
* `useAuthToken`: if this is set to false, no auth token is generated and used, and the connection can be 
  established by any process connecting to that port number. 

A GATE Slave started via the PythonSlaveLr keeps running until the resource is deleted or GATE is ended.


## Using the GATE Slave from Python

Once the PythonSlaveLr resource has been created it is ready to get used by a Python program:



```python
from gatenlp.gateslave import GateSlave
```

To connect to an already running slave process, the parameter `start=False` must be specified. 
In addition the auth token must be provided and the port and host, if they differ from the default.


```python
gs = GateSlave(start=False, auth_token="841e634a-d1f0-4768-b763-a7738ddee003")
```

The gate slave instance can now be used to run arbitrary Java methods on the Java side. 
The gate slave instance provides a number of useful methods directly (see [PythonDoc for gateslave](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/gateslave.html) )
* `gs.load_gdoc(filepath, mimetype=None`: load a GATE document on the Java side and return it to Python
* `gs.save_gdoc(gatedocument, filepath, mimetype=None)`: save a GATE document on the Java side
* `gs.gdoc2pdoc(gatedocument)`: convert the Java GATE document as a Python GateNLP document and return it
* `gs.pdoc2gdoc(doc)`: convert the Python GateNLP document to a Java GATE document and return it
* `gs.del_gdoc(gatedocument)`: remove a Java GATE document on the Java side (this necessary to release memory)
* `gs.load_pdoc(filepath, mimetype=None)`: load a document on the Java side using the file format specified via the mime type and return it as a Python GateNLP document
* `gs.log_actions(trueorfalse)`: switch logging of actions on the slave side off/on

In addition, there is a larger number of utility methods which are available through `gs.slave` (see 
[PythonSlave Source code](https://github.com/GateNLP/gateplugin-Python/blob/master/src/main/java/gate/plugin/python/PythonSlave.java), here are a few examples:

* `loadMavenPlugin(group, artifact, version)`: make the plugin identified by the given Maven coordinates available
* `loadPipelineFromFile(filepath)`: load the pipeline/controller from the given file path and return it
* `loadDocumentFromFile(filepath)`: load a GATE document from the file and return it
* `loadDocumentFromFile(filepath, mimetype)`: load a GATE document from the file using the format corresponding to the given mime type and return it
* `saveDocumentToFile(gatedocument, filepath, mimetype)`: save the document to the file, using the format corresponding to the mime type
* `createDocument(content)`: create a new document from the given String content and return it
* `run4Document(pipeline, document)`: run the given pipeline on the given document




```python
# Create a new Java document from a string
gdoc1 = gs.slave.createDocument("This is a 💩 document. It mentions Barack Obama and George Bush and New York.")
gdoc1
```




    JavaObject id=o0




```python
# you can call the API methods for the document directly from Python
print(gdoc1.getName())
print(gdoc1.getFeatures())
```

    GATE Document_00015
    {'gate.SourceURL': 'created from String'}



```python
# so far the document only "lives" in the Java process. In order to copy it to Python, it has to be converted
# to a Python GateNLP document:
pdoc1 = gs.gdoc2pdoc(gdoc1)
pdoc1.text
```




    'This is a 💩 document. It mentions Barack Obama and George Bush and New York.'




```python
# Let's load ANNIE on the Java side and run it on that document:
# First we have to load the ANNIE plugin:
gs.slave.loadMavenPlugin("uk.ac.gate.plugins", "annie", "8.6")
```


```python
# now load the prepared ANNIE pipeline from the plugin
pipeline = gs.slave.loadPipelineFromPlugin("uk.ac.gate.plugins","annie", "/resources/ANNIE_with_defaults.gapp")
pipeline.getName()
```




    'ANNIE'




```python
# run the pipeline on the document and convert it to a GateNLP Python document and display it
gs.slave.run4Document(pipeline, gdoc1)
pdoc1 = gs.gdoc2pdoc(gdoc1)

```


```python
pdoc1
```




<div><style>#KSGQEEQIKK-wrapper { color: black !important; }</style>
<div id="KSGQEEQIKK-wrapper">

<div>
<style>
#KSGQEEQIKK-content {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.KSGQEEQIKK-row {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.KSGQEEQIKK-col {
    border: 1px solid grey;
    display: inline-block;
    min-width: 200px;
    padding: 5px;
    /* white-space: normal; */
    /* white-space: pre-wrap; */
    overflow-y: auto;
}

.KSGQEEQIKK-hdr {
    font-size: 1.2rem;
    font-weight: bold;
}

.KSGQEEQIKK-label {
    margin-bottom: -15px;
    display: block;
}

.KSGQEEQIKK-input {
    vertical-align: middle;
    position: relative;
    *overflow: hidden;
}

#KSGQEEQIKK-popup {
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

.KSGQEEQIKK-selection {
    margin-bottom: 5px;
}

.KSGQEEQIKK-featuretable {
    margin-top: 10px;
}

.KSGQEEQIKK-fname {
    text-align: left !important;
    font-weight: bold;
    margin-right: 10px;
}
.KSGQEEQIKK-fvalue {
    text-align: left !important;
}
</style>
  <div id="KSGQEEQIKK-content">
        <div id="KSGQEEQIKK-popup" style="display: none;">
        </div>
        <div class="KSGQEEQIKK-row" id="KSGQEEQIKK-row1" style="height:67vh; min-height:100px;">
            <div id="KSGQEEQIKK-text-wrapper" class="KSGQEEQIKK-col" style="width:70%;">
                <div class="KSGQEEQIKK-hdr" id="KSGQEEQIKK-dochdr"></div>
                <div id="KSGQEEQIKK-text">
                </div>
            </div>
            <div id="KSGQEEQIKK-chooser" class="KSGQEEQIKK-col" style="width:30%; border-left-width: 0px;"></div>
        </div>
        <div class="KSGQEEQIKK-row" id="KSGQEEQIKK-row2" style="height:30vh; min-height: 100px;">
            <div id="KSGQEEQIKK-details" class="KSGQEEQIKK-col" style="width:100%; border-top-width: 0px;">
            </div>
        </div>
    </div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script><script src="https://unpkg.com/gatenlp-ann-viewer@1.0.11/gatenlp-ann-viewer.js"></script>
    <script type="application/json" id="KSGQEEQIKK-data">
    {"annotation_sets": {"": {"name": "detached-from:", "annotations": [{"type": "Token", "start": 0, "end": 4, "id": 1, "features": {"orth": "upperInitial", "string": "This", "kind": "word", "length": "4", "category": "DT"}}, {"type": "SpaceToken", "start": 4, "end": 5, "id": 2, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 5, "end": 7, "id": 3, "features": {"orth": "lowercase", "string": "is", "kind": "word", "length": "2", "category": "VBZ"}}, {"type": "SpaceToken", "start": 7, "end": 8, "id": 4, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 8, "end": 9, "id": 5, "features": {"orth": "lowercase", "string": "a", "kind": "word", "length": "1", "category": "DT"}}, {"type": "SpaceToken", "start": 9, "end": 10, "id": 6, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 10, "end": 12, "id": 7, "features": {"string": "\ud83d\udca9", "kind": "symbol", "length": "2", "category": "NN"}}, {"type": "SpaceToken", "start": 12, "end": 13, "id": 8, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 13, "end": 21, "id": 9, "features": {"orth": "lowercase", "string": "document", "kind": "word", "length": "8", "category": "NN"}}, {"type": "Token", "start": 21, "end": 22, "id": 10, "features": {"string": ".", "kind": "punctuation", "length": "1", "category": "."}}, {"type": "SpaceToken", "start": 22, "end": 23, "id": 11, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 23, "end": 25, "id": 12, "features": {"orth": "upperInitial", "string": "It", "kind": "word", "length": "2", "category": "PRP"}}, {"type": "SpaceToken", "start": 25, "end": 26, "id": 13, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 26, "end": 34, "id": 14, "features": {"orth": "lowercase", "string": "mentions", "kind": "word", "length": "8", "category": "VBZ"}}, {"type": "SpaceToken", "start": 34, "end": 35, "id": 15, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 35, "end": 41, "id": 16, "features": {"orth": "upperInitial", "string": "Barack", "kind": "word", "length": "6", "category": "NNP"}}, {"type": "SpaceToken", "start": 41, "end": 42, "id": 17, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 42, "end": 47, "id": 18, "features": {"orth": "upperInitial", "string": "Obama", "kind": "word", "length": "5", "category": "NNP"}}, {"type": "SpaceToken", "start": 47, "end": 48, "id": 19, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 48, "end": 51, "id": 20, "features": {"orth": "lowercase", "string": "and", "kind": "word", "length": "3", "category": "CC"}}, {"type": "SpaceToken", "start": 51, "end": 52, "id": 21, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 52, "end": 58, "id": 22, "features": {"orth": "upperInitial", "string": "George", "kind": "word", "length": "6", "category": "NNP"}}, {"type": "SpaceToken", "start": 58, "end": 59, "id": 23, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 59, "end": 63, "id": 24, "features": {"orth": "upperInitial", "string": "Bush", "kind": "word", "length": "4", "category": "NNP"}}, {"type": "SpaceToken", "start": 63, "end": 64, "id": 25, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 64, "end": 67, "id": 26, "features": {"orth": "lowercase", "string": "and", "kind": "word", "length": "3", "category": "CC"}}, {"type": "SpaceToken", "start": 67, "end": 68, "id": 27, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 68, "end": 71, "id": 28, "features": {"orth": "upperInitial", "string": "New", "kind": "word", "length": "3", "category": "NNP"}}, {"type": "SpaceToken", "start": 71, "end": 72, "id": 29, "features": {"string": " ", "kind": "space", "length": "1"}}, {"type": "Token", "start": 72, "end": 76, "id": 30, "features": {"orth": "upperInitial", "string": "York", "kind": "word", "length": "4", "category": "NNP"}}, {"type": "Token", "start": 76, "end": 77, "id": 31, "features": {"string": ".", "kind": "punctuation", "length": "1", "category": "."}}, {"type": "Lookup", "start": 0, "end": 4, "id": 32, "features": {"majorType": "time_modifier"}}, {"type": "Lookup", "start": 5, "end": 7, "id": 33, "features": {"majorType": "country_code"}}, {"type": "Lookup", "start": 23, "end": 25, "id": 34, "features": {"majorType": "stop"}}, {"type": "Lookup", "start": 35, "end": 47, "id": 35, "features": {"majorType": "person_full", "gender": "male"}}, {"type": "Lookup", "start": 42, "end": 47, "id": 36, "features": {"majorType": "person_full", "gender": "male"}}, {"type": "Lookup", "start": 52, "end": 63, "id": 37, "features": {"majorType": "person_full", "gender": "male"}}, {"type": "Lookup", "start": 68, "end": 76, "id": 38, "features": {"majorType": "location", "minorType": "city"}}, {"type": "Lookup", "start": 72, "end": 76, "id": 39, "features": {"majorType": "location", "minorType": "city"}}, {"type": "Split", "start": 21, "end": 22, "id": 40, "features": {"kind": "internal"}}, {"type": "Split", "start": 76, "end": 77, "id": 41, "features": {"kind": "internal"}}, {"type": "Sentence", "start": 0, "end": 22, "id": 42, "features": {}}, {"type": "Sentence", "start": 23, "end": 77, "id": 43, "features": {}}, {"type": "Person", "start": 35, "end": 47, "id": 56, "features": {"firstName": "Barack", "ruleFinal": "PersonFinal", "gender": "male", "surname": "Obama", "kind": "fullName", "rule": "GazPerson"}}, {"type": "Person", "start": 52, "end": 63, "id": 57, "features": {"firstName": "George", "ruleFinal": "PersonFinal", "gender": "male", "surname": "Bush", "kind": "fullName", "rule": "GazPerson"}}, {"type": "Location", "start": 68, "end": 76, "id": 58, "features": {"ruleFinal": "LocFinal", "rule": "Location1", "locType": "city"}}], "next_annid": 59}}, "text": "This is a \ud83d\udca9 document. It mentions Barack Obama and George Bush and New York.", "features": {"gate.SourceURL": "created from String"}, "offset_type": "j", "name": ""}
    </script>
    <script type="text/javascript">
        gatenlp_run("KSGQEEQIKK-");
    </script>
  </div>

</div></div>



## Manually starting the GATE Slave from Python

After installation of Python `gatenlp`, the command `gatenlp-gate-slave` is available. 

You can run `gatenlp-gate-slave --help` to get help information:

```
usage: gatenlp-gate-slave [-h] [--port PORT] [--host HOST] [--auth AUTH]
                          [--noauth] [--gatehome GATEHOME]
                          [--platform PLATFORM] [--log_actions] [--keep]

Start Java GATE Slave

optional arguments:
  -h, --help           show this help message and exit
  --port PORT          Port (25333)
  --host HOST          Host to bind to (127.0.0.1)
  --auth AUTH          Auth token to use (generate random)
  --noauth             Do not use auth token
  --gatehome GATEHOME  Location of GATE (environment variable GATE_HOME)
  --platform PLATFORM  OS/Platform: windows or linux (autodetect)
  --log_actions        If slave actions should be logged
  --keep               Prevent shutting down the slave
```

For example to start a gate slave as with the PythonSlaveLr above, but this time re-using the exact same
auth token and switching on logging of the actions:
    
```
gatenlp-gate-slave --auth 841e634a-d1f0-4768-b763-a7738ddee003 --log_actions
```

Again the Python program can connect to the server as before:



```python
gs = GateSlave(start=False, auth_token="841e634a-d1f0-4768-b763-a7738ddee003")
gs
```




    <gatenlp.gateslave.GateSlave at 0x7fcf544e9b90>



The GATE slave started that way keeps running until it is interrupted from the keyboard using "Ctrl-C" or 
until the GATE slave sends the "close" request:


```python
gs.close()
```

## Automatically starting the GATE Slave from Python

When using the GateSlave class from python, it is possible to just start the slave processes automatically in the background by setting the paramater `start` to `True`:


```python
gs = GateSlave(start=True, auth_token="my-super-secret-auth-token")
```

    Trying to start GATE Slave on port=25333 host=127.0.0.1 log=false keep=false
    PythonSlaveRunning: starting server with 25333/127.0.0.1/my-super-secret-auth-token/false



```python
gdoc1 = gs.slave.createDocument("This is a 💩 document. It mentions Barack Obama and George Bush and New York.")
gdoc1
```




    JavaObject id=o0




```python
# when done, the gate slave should get closed:
gs.close()
```
