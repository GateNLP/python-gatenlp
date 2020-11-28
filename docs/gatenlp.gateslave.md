<a name="gatenlp.gateslave"></a>
# gatenlp.gateslave

Module for interacting with a Java GATE process, running API commands on it and
exchanging data with it.

<a name="gatenlp.gateslave.classpath_sep"></a>
#### classpath\_sep

```python
classpath_sep(platform=None)
```

Get the system-specific classpath separator character.

**Arguments**:

- `platform` - (Default value = None) win/windows for Windows, anything else for non-windows
  If not specified, tries to determine automatically (which may fail)
  

**Returns**:

  classpath separator character

<a name="gatenlp.gateslave.gate_classpath"></a>
#### gate\_classpath

```python
gate_classpath(gatehome, platform=None)
```

Return the GATE classpath components as a string, with the path seperator characters appropriate
for the operating system.

**Arguments**:

- `gatehome` - where GATE is installed, either as a cloned git repo or a downloaded installation dir.
- `platform` - (Default value = None) win/windows for Windows, anything else for non-Windows.
  

**Returns**:

  GATE classpath
  

**Raises**:

  Exception if classpath could not be determined.

<a name="gatenlp.gateslave.start_gate_slave"></a>
#### start\_gate\_slave

```python
start_gate_slave(port=25333, host="127.0.0.1", auth_token=None, use_auth_token=True, java="java", platform=None, gatehome=None, log_actions=False, keep=False, debug=False)
```

Run the gate slave program. This starts the Java program included with gatenlp to
run GATE and execute the gate slave within GATE so that Python can connect to it.

**Arguments**:

- `port` - (Default value = 25333) Port number to use
- `host` - (Default value = "127.0.0.1") Host address to bind to
- `auth_token` - (Default value = None)  Authorization token to use. If None, creates a random token.
- `use_auth_token` - (Default value = True) If False, do not aue an authorization token at all.
  This allows anyone who can connect to the host address to connect and use the gate slave process.
- `java` - (Default value = "java") Java command (if on the binary path) or full path to the binary
  to use for running the gate slave program.
- `platform` - (Default value = None) "win"/"windows" for Windows, anything else for non-Windows.
  If None, tries to determine automatically.
- `gatehome` - (Default value = None) The path to where GATE is installed. If None, the environment
  variable "GATE_HOME" is used.
- `log_actions` - (Default value = False) If True, the GATE Slave process will log everything it is
  ordered to do.
- `keep` - (Default value = False) passed on to the gate slave process and tells the process if it should
  report to the using Pythong process that it can be closed or not.
- `debug` - (Default valuye = False) Show debug messages.

<a name="gatenlp.gateslave.GateSlave"></a>
## GateSlave Objects

```python
class GateSlave()
```

Gate slave for remotely running arbitrary GATE and other JAVA operations in a separate
Java GATE process.

<a name="gatenlp.gateslave.GateSlave.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(port=25333, start=True, java="java", host="127.0.0.1", gatehome=None, platform=None, auth_token=None, use_auth_token=True, log_actions=False, keep=False, debug=False)
```

Create an instance of the GateSlave and either start our own Java GATE process for it to use
(start=True) or connect to an existing one (start=False).

After the GateSlave instance has been create successfully, it is possible to:

* Use one of the methods of the instance to perform operations on the Java side or exchange data

* use GateSlave.slave to invoke methods from the PythonSlave class on the Java side

* use GateSlave.jvm to directly construct objects or call instance or static methods

NOTE: the GATE process must not output anything important/big to stderr because everything from
stderr gets captured and used for communication between the Java and Python processes. At least
part of the output to stderr may only be passed on after the GATE process has ended.

**Example**:

  
  ```python
  gs = GateSlave()
  pipeline = gs.slave.loadPipelineFromFile("thePipeline.xgapp")
  doc = gs.slave.createDocument("Some document text")
  gs.slave.run4doc(pipeline,doc)
  pdoc = gs.gdoc2pdoc(doc)
  gs.slave.deleteResource(doc)
  # process the document pdoc ...
  ```
  
- `port` - port to use
- `start` - if True, try to start our own GATE process, otherwise expect an already started
  process at the host/port address
- `java` - path to the java binary to run or the java command to use from the PATH (for start=True)
- `host` - host an existing Java GATE process is running on (only relevant for start=False)
- `gatehome` - where GATE is installed (only relevant if start=True). If None, expects
  environment variable GATE_HOME to be set.
- `platform` - system platform we run on, one of Windows, Linux (also for MacOs) or Java
- `auth_token` - if None or "" and use_auth_token is True, generate a random token which
  is then accessible via the auth_token attribute, otherwise use the given auth token.
- `use_auth_token` - if False, do not use an auth token, otherwise either use the one specified
  via auth_token or generate a random one.
- `log_actions` - if the gate slave should log the actions it is doing
- `keep` - normally if gs.close() is called and we are not connected to the PythonSlaveLr,
  the slave will be shut down. If this is True, the gs.close() method does not shut down
  the slave.
- `debug` - show debug messages (default: False)

<a name="gatenlp.gateslave.GateSlave.download"></a>
#### download

```python
 | @staticmethod
 | download()
```

Download GATE libraries into a standard location so we can run the GATE slave even if GATE_HOME
is not set.

NOTE YET IMPLEMENTED.

<a name="gatenlp.gateslave.GateSlave.close"></a>
#### close

```python
 | close()
```

Clean up: if the gate slave process was started by us, we will shut it down.
Otherwise we can still close it if it was started by the slaverunner, not the Lr
Note: if it was started by us, it was started via the slaverunner.

<a name="gatenlp.gateslave.GateSlave.log_actions"></a>
#### log\_actions

```python
 | log_actions(onoff)
```

Swith logging actions at the slave on or off.

**Arguments**:

- `onoff` - True to log actions, False to not log them

<a name="gatenlp.gateslave.GateSlave.load_gdoc"></a>
#### load\_gdoc

```python
 | load_gdoc(path, mimetype=None)
```

Let GATE load a document from the given path and return a handle to it.

**Arguments**:

- `path` - path to the gate document to load.
- `mimetype` - a mimetype to use when loading. (Default value = None)
  

**Returns**:

  a handle to the Java GATE document

<a name="gatenlp.gateslave.GateSlave.save_gdoc"></a>
#### save\_gdoc

```python
 | save_gdoc(gdoc, path, mimetype=None)
```

Save GATE document to the given path.

**Arguments**:

- `gdoc` - GATE document handle
- `path` - destination path
- `mimetype` - mimtetype, only the following types are allowed: ""/None: GATE XML,
  application/fastinfoset, and all mimetypes supported by the
  Format_Bdoc plugin. (Default value = None)

<a name="gatenlp.gateslave.GateSlave.gdoc2pdoc"></a>
#### gdoc2pdoc

```python
 | gdoc2pdoc(gdoc)
```

Convert the GATE document to a python document and return it.

**Arguments**:

- `gdoc` - the handle to a GATE document
  

**Returns**:

  a gatenlp Document instance

<a name="gatenlp.gateslave.GateSlave.pdoc2gdoc"></a>
#### pdoc2gdoc

```python
 | pdoc2gdoc(pdoc)
```

Convert the Python gatenlp document to a GATE document and return a handle to it.

**Arguments**:

- `pdoc` - python gatenlp Document
  

**Returns**:

  handle to GATE document

<a name="gatenlp.gateslave.GateSlave.load_pdoc"></a>
#### load\_pdoc

```python
 | load_pdoc(path, mimetype=None)
```

Load a document from the given path, using GATE and convert and return as gatenlp Python document.

**Arguments**:

- `path` - path to load document from
- `mimetype` - mime type to use (Default value = None)
  

**Returns**:

  gatenlp document

<a name="gatenlp.gateslave.GateSlave.del_resource"></a>
#### del\_resource

```python
 | del_resource(resource)
```

Delete/unload a GATE resource (Document, Corpus, ProcessingResource etc) from GATE.
This is particularly important to do when processing a large number of documents for each document
that is finished processing, otherwise the documents
will accumulate in the Java process and eat up all memory. NOTE: just removing all references to a
GATE document does not delete/unload the document!

**Arguments**:

- `resource` - the Java GATE resource, e.g. a document to remove

<a name="gatenlp.gateslave.GateSlave.show_gui"></a>
#### show\_gui

```python
 | show_gui()
```

Show the GUI for the started GATE process.

NOTE: this is more of a hack and may cause sync problems
when closing down the GATE slave.

<a name="gatenlp.gateslave.GateSlaveAnnotator"></a>
## GateSlaveAnnotator Objects

```python
class GateSlaveAnnotator(Annotator)
```

<a name="gatenlp.gateslave.GateSlaveAnnotator.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(pipeline, gatehome=None, port=25333, sets_send=None, sets_receive=None, replace_anns=False)
```

Create a GateSlave annotator.

This starts the gate slave, loads the pipeline and
can then be used to annotate Python gatenlp Document instances with the Java GATE
pipeline.

Note: to make sure tha start/finish callbacks on the Java side are invoked, the annotator
start() method should be invoked once before processing documents and finish() should
get called once after processing documents.

If the GateSlaveAnnotator is not used any more, close() should be invoked to terminate
the Java GATE Slave process.

**Example**:

  
  ```python
  pipeline = GateSlaveAnnotator("annie.xgapp")
  for idx, doc in enumerate(mycorpus):
  corpus[idx] = pipeline(doc)
  ```
  

**Arguments**:

- `pipeline` - the path to a Java GATE pipeline to load into the GATE slave
- `gatehome` - the gate home directory to use, if not set, uses environment variable GATE_HOME
- `port` - the port to use (25333)
- `sets_send` - a dictionary where the keys are the name of the target annotation set at the
  Java side and the values are either the source annotation set name or a list of
  tuples of the form (setname, typename).
- `sets_receive` - a dictionary where the keys are the name of the target annotation set at the
  Python side and the values are either the source annotation set name in Java or ta list
  of tuples of the form (setname, typename).
  replace_anns (default: False) if True, existing annotations (in the sets, of the types
  specified in sets_receive or all) are removed before the retrieved annotations are added.
  In this case, the annotation ids of the retrieved annotations are kept.
  If False, the retrieved annotations are added to the existing sets and may get new, different
  annotation ids.

<a name="gatenlp.gateslave.GateSlaveAnnotator.close"></a>
#### close

```python
 | close()
```

Shut down the GateSlave used by this annotator.

After calling this, the GateSlaveAnnotator instance cannot be used any more.

<a name="gatenlp.gateslave.GateSlaveAnnotator.start"></a>
#### start

```python
 | start()
```

Invoke the controller execution started method on the GATE controller.

<a name="gatenlp.gateslave.GateSlaveAnnotator.finish"></a>
#### finish

```python
 | finish()
```

Invoke the controller execution finished method on the GATE controller.

<a name="gatenlp.gateslave.GateSlaveAnnotator.__call__"></a>
#### \_\_call\_\_

```python
 | __call__(doc, **kwargs)
```

Run the GATE controller on the given document.

This runs the GATE pipeline (controller) on the given document by first sending the document
to the GATE process and coverting it to a GATE document there, running the pipeline on it,
and sending the document back and converting back to a new gatenlp Document.

IMPORTANT: the exact way of how the final document that gets returned by this method is created
may change or depend on how the annotator is configured: it may or may not be the original document
which gets modified in place or new document with the original document unchanged.

**Arguments**:

- `doc` - the document to process
- `**kwargs` - ignored so far
  

**Returns**:

  the processed gatenlp document which may be the original one passed to this method
  or a new one.

<a name="gatenlp.gateslave.main"></a>
#### main

```python
main()
```

Start a GATE slave from the command line.

This is available as command `gatenlp-gate-slave`.
Use option `--help` to get help about command line arguments.

