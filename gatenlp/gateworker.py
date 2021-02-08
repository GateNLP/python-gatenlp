#!/usr/bin/env python
"""
Module for interacting with a Java GATE process, running API commands on it and
exchanging data with it.
"""

import sys
import subprocess
import os
import platform as sysplatform
import logging
import atexit
import secrets
import argparse
import signal
import glob
import json
from gatenlp.annotation_set import AnnotationSet

# NOTE: we delay importing py4j to the class initializer. This allows us to make GateWorker available via gatenlp
# but does not force everyone to actually have py4j installed if they do not use the GateWorker
# from py4j.java_gateway import JavaGateway, GatewayParameters
from gatenlp import Document
from gatenlp.utils import init_logger
from gatenlp.processing.annotator import Annotator

JARVERSION = "1.0"

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

__pdoc__ = {"GateWorkerAnnotator.__call__": True}


def classpath_sep(platform=None):
    """
    Get the system-specific classpath separator character.

    Args:
      platform:  (Default value = None) win/windows for Windows, anything else for non-windows
        If not specified, tries to determine automatically (which may fail)

    Returns:
      classpath separator character

    """
    if not platform:
        myplatform = sysplatform.system()
        if not myplatform:
            raise Exception(
                "Could not determine operating system, please use platform parameter"
            )
        platform = myplatform
    if platform.lower() == "windows" or platform.lower() == "win":
        return ";"
    else:
        return ":"


def gate_classpath(gatehome, platform=None):
    """
    Return the GATE classpath components as a string, with the path seperator characters appropriate
    for the operating system.

    Args:
      gatehome: where GATE is installed, either as a cloned git repo or a downloaded installation dir.
      platform:  (Default value = None) win/windows for Windows, anything else for non-Windows.

    Returns:
      GATE classpath

    Raises:
        Exception if classpath could not be determined.

    """
    # check which kind of GATE home we have: if there is a distro subdirectory, assume cloned git repo
    if not os.path.exists(gatehome):
        raise Exception("GATE home directory does not exist: {}".format(gatehome))
    if not os.path.isdir(gatehome):
        raise Exception("GATE home directory does not a directory: {}".format(gatehome))
    cpsep = classpath_sep(platform)
    cpfile = os.path.join(gatehome, "gate.classpath")
    bindir = os.path.join(gatehome, "bin")
    # logger.info("DEBUG checking for {}".format(cpfile))
    if os.path.exists(cpfile):
        if not os.path.exists(cpfile):
            raise Exception(
                "File not found {}, distribution may need compiling".format(cpfile)
            )
        with open(cpfile, "rt", encoding="utf-8") as fp:
            cp = fp.read()
            return cp + cpsep + bindir
    else:
        # logger.info("DEBUG {} does not exist".format(cpfile))
        libdir = os.path.join(gatehome, "lib")
        bindir = os.path.join(gatehome, "bin")
        if not os.path.isdir(libdir):
            raise Exception(
                "Could not determine class path from {}, no lib directory".format(
                    gatehome
                )
            )
        jars = glob.glob(os.path.join(libdir, "*.jar"))
        libcp = cpsep.join(jars)

        return libcp + cpsep + bindir


def start_gate_worker(
    port=25333,
    host="127.0.0.1",
    auth_token=None,
    use_auth_token=True,
    java="java",
    platform=None,
    gatehome=None,
    log_actions=False,
    keep=False,
    debug=False,
):
    """
    Run the gate worker program. This starts the Java program included with gatenlp to
    run GATE and execute the gate worker within GATE so that Python can connect to it.

    Args:
      port:  (Default value = 25333) Port number to use
      host:  (Default value = "127.0.0.1") Host address to bind to
      auth_token:  (Default value = None)  Authorization token to use. If None, creates a random token.
      use_auth_token:  (Default value = True) If False, do not aue an authorization token at all.
         This allows anyone who can connect to the host address to connect and use the gate worker process.
      java:  (Default value = "java") Java command (if on the binary path) or full path to the binary
         to use for running the gate worker program.
      platform:  (Default value = None) "win"/"windows" for Windows, anything else for non-Windows.
         If None, tries to determine automatically.
      gatehome:  (Default value = None) The path to where GATE is installed. If None, the environment
         variable "GATE_HOME" is used.
      log_actions:  (Default value = False) If True, the GATE Worker process will log everything it is
         ordered to do.
      keep:  (Default value = False) passed on to the gate worker process and tells the process if it should
         report to the using Pythong process that it can be closed or not.
      debug: (Default valuye = False) Show debug messages.
    """
    logger = init_logger(__name__)
    if debug:
        logger.setLevel(logging.DEBUG)

    if gatehome is None:
        gatehome = os.environ.get("GATE_HOME")
        if gatehome is None:
            raise Exception(
                "Parameter gatehome is None and environment var GATE_HOME not set"
            )
    if use_auth_token:
        if not auth_token:
            auth_token = secrets.token_urlsafe(20)
        else:
            auth_token = auth_token
    else:
        auth_token = ""
    if log_actions:
        log_actions = "1"
    else:
        log_actions = "0"
    if keep:
        keep = "1"
    else:
        keep = "0"
    logger.debug(
        f"Starting gate worker, gatehome={gatehome}, auth_token={auth_token}, log_actions={log_actions}, keep={keep}"
    )
    jarloc = os.path.join(
        os.path.dirname(__file__), "_jars", f"gatetools-gatenlpworker-{JARVERSION}.jar"
    )
    if not os.path.exists(jarloc):
        raise Exception("Could not find jar, {} does not exist".format(jarloc))
    logger.debug(f"Using JAR: {jarloc}")
    cmdandparms = [java, "-cp"]
    cpsep = classpath_sep(platform=platform)
    cmdandparms.append(jarloc + cpsep + gate_classpath(gatehome, platform=platform))
    cmdandparms.append("gate.tools.gatenlpworker.GatenlpWorker")
    cmdandparms.append(str(port))
    cmdandparms.append(host)
    cmdandparms.append(log_actions)
    cmdandparms.append(keep)
    os.environ["GATENLP_WORKER_TOKEN_" + str(port)] = auth_token
    cmd = " ".join(cmdandparms)
    logger.debug(f"Running command: {cmd}")
    subproc = subprocess.Popen(
        cmdandparms, stderr=subprocess.PIPE, bufsize=0, encoding="utf-8"
    )

    def shutdown():
        """
        Handler that gets invoked when the calling Python program exits.
        This terminates the gate worker by sending the SIGINT signal to it.
        """
        subproc.send_signal(signal.SIGINT)
        for line in subproc.stderr:
            print(line, file=sys.stderr, end="")

    atexit.register(shutdown)
    while True:
        line = subproc.stderr.readline()
        if line == "":
            break
        line = line.rstrip("\n\r")
        if line == "PythonWorkerRunner.java: server start OK":
            break
        if line == "PythonWorkerRunner.java: server start NOT OK":
            raise Exception("Could not start server, giving up")
        print(line, file=sys.stderr)
    try:
        subproc.wait()
    except KeyboardInterrupt:
        print("Received keyboard interrupt, shutting down server...")
        shutdown()


class GateWorker:
    """
    Gate worker for remotely running arbitrary GATE and other JAVA operations in a separate
    Java GATE process.
    """

    def __init__(
        self,
        port=25333,
        start=True,
        java="java",
        host="127.0.0.1",
        gatehome=None,
        platform=None,
        auth_token=None,
        use_auth_token=True,
        log_actions=False,
        keep=False,
        debug=False,
    ):
        """
        Create an instance of the GateWorker and either start our own Java GATE process for it to use
        (start=True) or connect to an existing one (start=False).

        After the GateWorker instance has been create successfully, it is possible to:

        * Use one of the methods of the instance to perform operations on the Java side or exchange data

        * use GateWorker.worker to invoke methods from the PythonWorker class on the Java side

        * use GateWorker.jvm to directly construct objects or call instance or static methods

        NOTE: the GATE process must not output anything important/big to stderr because everything from
        stderr gets captured and used for communication between the Java and Python processes. At least
        part of the output to stderr may only be passed on after the GATE process has ended.

        Example:

            ```python
            gs = GateWorker()
            pipeline = gs.worker.loadPipelineFromFile("thePipeline.xgapp")
            doc = gs.worker.createDocument("Some document text")
            gs.worker.run4doc(pipeline,doc)
            pdoc = gs.gdoc2pdoc(doc)
            gs.worker.deleteResource(doc)
            # process the document pdoc ...
            ```

        port: port to use
        start: if True, try to start our own GATE process, otherwise expect an already started
           process at the host/port address
        java: path to the java binary to run or the java command to use from the PATH (for start=True)
        host: host an existing Java GATE process is running on (only relevant for start=False)
        gatehome: where GATE is installed (only relevant if start=True). If None, expects
               environment variable GATE_HOME to be set.
        platform: system platform we run on, one of Windows, Linux (also for MacOs) or Java
        auth_token: if None or "" and use_auth_token is True, generate a random token which
               is then accessible via the auth_token attribute, otherwise use the given auth token.
        use_auth_token: if False, do not use an auth token, otherwise either use the one specified
               via auth_token or generate a random one.
        log_actions: if the gate worker should log the actions it is doing
        keep: normally if gs.close() is called and we are not connected to the PythonWorkerLr,
               the worker will be shut down. If this is True, the gs.close() method does not shut down
               the worker.
        debug: show debug messages (default: False)
        """
        self.logger = init_logger(__name__)

        from py4j.java_gateway import JavaGateway, GatewayParameters

        self.gatehome = gatehome
        self.port = port
        self.host = host
        self.start = start
        self.gatehome = gatehome
        self.platform = platform
        self.gateprocess = None
        self.gateway = None
        self.worker = None
        self.closed = False
        self.keep = keep
        self.debug = debug
        self.log_actions = log_actions
        if use_auth_token:
            if not auth_token:
                self.auth_token = secrets.token_urlsafe(20)
            else:
                self.auth_token = auth_token
        else:
            self.auth_token = ""
        if gatehome is None and start:
            gatehome = os.environ.get("GATE_HOME")
            if gatehome is None:
                raise Exception(
                    "Parameter gatehome is None and environment var GATE_HOME not set"
                )
            self.gatehome = gatehome
        if start:
            # make sure we find the jar we need
            # logger.info("DEBUG: file location: {}".format(__file__))
            jarloc = os.path.join(
                os.path.dirname(__file__),
                "_jars",
                f"gatetools-gatenlpworker-{JARVERSION}.jar",
            )
            if not os.path.exists(jarloc):
                raise Exception("Could not find jar, {} does not exist".format(jarloc))
            cmdandparms = [java, "-cp"]
            cpsep = classpath_sep(platform=platform)
            cmdandparms.append(
                jarloc + cpsep + gate_classpath(self.gatehome, platform=platform)
            )
            cmdandparms.append("gate.tools.gatenlpworker.GatenlpWorker")
            cmdandparms.append(str(port))
            cmdandparms.append(host)
            if log_actions:
                cmdandparms.append("1")
            else:
                cmdandparms.append("0")
            if keep:
                cmdandparms.append("1")
            else:
                cmdandparms.append("0")
            os.environ["GATENLP_WORKER_TOKEN_" + str(self.port)] = self.auth_token
            cmd = " ".join(cmdandparms)
            self.logger.debug(f"Running command: {cmd}")
            subproc = subprocess.Popen(
                cmdandparms, stderr=subprocess.PIPE, bufsize=0, encoding="utf-8"
            )
            self.gateprocess = subproc
            while True:
                line = subproc.stderr.readline()
                if line == "":
                    break
                line = line.rstrip("\n\r")
                if line == "PythonWorkerRunner.java: server start OK":
                    break
                if line == "PythonWorkerRunner.java: server start NOT OK":
                    raise Exception("Could not start server, giving up")
                print(line, file=sys.stderr)
            atexit.register(self.close)
        self.gateway = JavaGateway(
            gateway_parameters=GatewayParameters(port=port, auth_token=self.auth_token)
        )
        self.jvm = self.gateway.jvm
        self.worker = self.gateway.entry_point
        self.gate_version = self.jvm.gate.Main.version
        self.gate_build = self.jvm.gate.Main.build
        self.worker_version = self.worker.pluginVersion()
        self.worker_build = self.worker.pluginBuild()

    @staticmethod
    def download():
        """
        Download GATE libraries into a standard location so we can run the GATE worker even if GATE_HOME
        is not set.

        NOTE YET IMPLEMENTED.
        """
        # TODO: this should use the command and bootstrapping jar in gate-downloader:
        # copy the whole directory into the standard per-user config directory for the system
        # run the command
        # use the generated gate.classpath as for a compiled local git repo
        # NOTE: should change error message if GATE_HOME is not set to hint at this! (option --downlaod for the script)
        # NOTE: add to documentation
        raise Exception("Not yet implemented")

    def close(self):
        """
        Clean up: if the gate worker process was started by us, we will shut it down.
        Otherwise we can still close it if it was started by the workerrunner, not the Lr
        Note: if it was started by us, it was started via the workerrunner.
        """
        if not self.closed and self.worker.isClosable():
            self.closed = True
            self.gateway.shutdown()
            if self.gateprocess is not None:
                for line in self.gateprocess.stderr:
                    print(line, file=sys.stderr, end="")
                self.gateprocess.wait()

    def log_actions(self, onoff):
        """
        Switch logging actions at the worker on or off.

        Args:
          onoff: True to log actions, False to not log them
        """
        self.worker.logActions(onoff)

    def load_gdoc(self, path, mimetype=None):
        """
        Let GATE load a document from the given path and return a handle to it.

        Args:
          path: path to the gate document to load.
          mimetype: a mimetype to use when loading. (Default value = None)

        Returns:
          a handle to the Java GATE document
        """
        if mimetype is None:
            mimetype = ""
        return self.worker.loadDocumentFromFile(path, mimetype)

    def save_gdoc(self, gdoc, path, mimetype=None):
        """
        Save GATE document to the given path.

        Args:
          gdoc: GATE document handle
          path: destination path
          mimetype: mimtetype, only the following types are allowed: ""/None: GATE XML,
                application/fastinfoset, and all mimetypes supported by the
                Format_Bdoc plugin. (Default value = None)
        """
        if mimetype is None:
            mimetype = ""
        self.worker.saveDocumentToFile(path, mimetype)

    def gdoc2pdoc(self, gdoc):
        """
        Convert the GATE document to a python document and return it.

        Args:
          gdoc: the handle to a GATE document

        Returns:
          a gatenlp Document instance
        """
        bjs = self.worker.getBdocJson(gdoc)
        return Document.load_mem(bjs, fmt="bdocjs")

    def pdoc2gdoc(self, pdoc, annsets=None):
        """
        Convert the Python gatenlp document to a GATE document and return a handle to it.

        Args:
            pdoc: python gatenlp Document
            annsets: a list of either set names, or tuples where the first element is a set name and the
                second element is either a type name or a list of type names.

        Returns:
            handle to GATE document
        """
        json = pdoc.save_mem(fmt="bdocjs", annsets=annsets)
        return self.worker.getDocument4BdocJson(json)

    def gdocanns2pdoc(self, gdoc, pdoc, annsets=None, replace=False):
        """
        Retrieve the annotations from the GATE document and add them to the python gatenlp document.
        This modifies the pdoc in place and returns it.

        Args:
            gdoc: a handle to a Java GATE document
            pdoc: Python gatenlp document
            annsets: if not None, an annotation specification: a list of set names or tuples where the first
                element is a set name and the second element is either a type name or a list of type names
            replace: if True, replaces all annotations with the same set and annotation id, otherwise adds
                annotaitons with potentially a new annotation id.

        Returns:
            the modified pdoc
        """
        # to make it easier on the Java side to interpret the annsets specification, convert it so that
        # all elements are a list where first element is always the set name and all remaining elements
        # are tyepe names. If there is one remaining element which is null, include all types for that set.
        newannsets = self.pannsets2gannsets(annsets)
        # now retrieve the BDOC JSON representation of the annotations
        thejson = self.jsonAnnsets4Doc(gdoc, newannsets)
        dictrep = json.loads(thejson)
        for name, adict in dictrep.items():
            annset = AnnotationSet.from_dict(adict, owner_doc=None)
            targetset = pdoc.annset(name)
            # add the annotations in annset to the pdoc, depending on replace
            for ann in annset._annotations.values():
                # if the annotation id already exists in the target set, proceed according to replace,
                # if not, just add it as is
                if ann.id in targetset._annotations:
                    if replace:
                        # for now, the simplified version: remove existing add new
                        targetset.remove(ann.id)
                        targetset.add_ann(ann, annid=ann.id)
                    else:
                        targetset.add_ann(ann)
                else:
                    targetset.add_ann(ann)
        return pdoc

    def load_pdoc(self, path, mimetype=None):
        """
        Load a document from the given path, using GATE and convert and return as gatenlp Python document.

        Args:
          path: path to load document from
          mimetype: mime type to use (Default value = None)

        Returns:
          gatenlp document
        """
        gdoc = self.load_gdoc(path, mimetype)
        return self.gdoc2pdoc(gdoc)

    def del_resource(self, resource):
        """
        Delete/unload a GATE resource (Document, Corpus, ProcessingResource etc) from GATE.
        This is particularly important to do when processing a large number of documents for each document
        that is finished processing, otherwise the documents
        will accumulate in the Java process and eat up all memory. NOTE: just removing all references to a
        GATE document does not delete/unload the document!

        Args:
          resource: the Java GATE resource, e.g. a document to remove
        """
        self.jvm.gate.Factory.deleteResource(resource)

    def show_gui(self):
        """
        Show the GUI for the started GATE process.

        NOTE: this is more of a hack and may cause sync problems
        when closing down the GATE worker.
        """
        self.worker.showGui()

    # methods that mirror the methods from the Java gate.plugin.python.PythonWorker methods
    # These could get called directly via gs.worker.METHODNAME calls but are implemented here
    # to provide easier discovery and better documentation on the Python side
    # Since these are really local mirrors of Java methods, they follow Java naming conventions
    def createDocument(self, content):
        """
        Create a Java GATE document from the content string and return a handle to it.

        Args:
            content: the text of the document

        Returns:
            handle to Java GATE document
        """
        return self.worker.createDocument(content)

    def deleteResource(self, resource):
        """
        Remove a Java GATE resource and release its memory.

        Args:
            resource: a handle to some Java GATE resource
        """
        self.worker.deleteResource(resource)

    def findMavenPlugin(self, group, artifact):
        """
        Find a Java GATE Maven plugin and return a handle to it, or None if nothing found.

        Args:
            group: the Maven group for the plugin
            artifact: the artifact name for the plugin

        Returns:
            a handle to the plugin or None if not found
        """
        return self.worker.findMavenPlugin(group, artifact)

    def gate_build(self):
        """
        Return the short commit id of the Java GATE we are connected to.

        Returns:
            short commit id string
        """
        return self.worker.gate_build()

    def gate_version(self):
        """
        Return the version string of the Java GATE we are connected to.

        Returns:
            version string
        """
        return self.worker.gate_version()

    def getBdocJson(self, gdoc):
        """
        Return the Bdoc JSON serialization of a Java GATE document as string.

        Args:
            gdoc: a handle to a GATE document

        Returns:
            BDOC serialization JSON string
        """
        return self.worker.getBdocJson(gdoc)

    def getCorpus4Name(self, name):
        """
        Return a handle to the first Java GATE corpus with the given name or None if none found.

        Args:
            name: corpus name

        Returns:
            first matching corpus or None
        """
        return self.worker.getCorpus4Name(name)

    def getCorpusNames(self):
        """
        Return a list of all Java GATE corpus names known.

        Returns:
            list of corpus names
        """
        return self.worker.getCorpusNames()

    def getDocument4BdocJson(self, bdocjson):
        """
        Returns a handle to a Java GATE document created from the Bdoc JSON string.

        Args:
            bdocjson: a BDOC JSON string

        Returns:
            handle to the Java GATE document
        """
        return self.worker.getDocument4BdocJson

    def getDocument4Name(self, name):
        """
        Return a handle to the first Java GATE document that has the given name or None if none found.

        Args:
            name: the document name

        Returns:
            a handle to the Java GATE document
        """
        return self.worker.getDocument4Name(name)

    def getDocumentNames(self):
        """
        Return a list of known Java GATE document names.

        Returns:
            list of Java GATE document names
        """
        return self.worker.getDocumentNames()

    def getPipeline4Name(self, name):
        """
        Return a handle to the first Java GATE pipeline/controller that has the given name or
        None if none found.

        Args:
            name: name of the pipeline

        Returns:
            handle to the pipeline
        """
        return self.worker.getPipeline4Name(name)

    def getPipelineNames(self):
        """
        Return a list of all know Java GATE pipeline names.

        Returns:
            list of pipeline names
        """
        return self.worker.getPipelineNames()

    def getPr4Name(self, name):
        """
        Return a handle to the first Java GATE processing resource that has the given name
        or None if none found.

        Args:
            name: the name of the processing resource

        Returns:
            a handle to the processing resource or None
        """
        return self.worker.getPr4Name(name)

    def getPrNames(self):
        """
        Return a list of known Java GATE  processing resource names.

        Returns:
            list of PR names
        """
        return self.worker.getPrNames()

    def getResources4Name(self, name):
        """
        Return a (possibly empty) list of all Java GATE resources with the given name.

        Args:
            name: name of the resources

        Returns:
            list of matching resources
        """
        return self.worker.getResources4Name(name)


    def getResources4NameClass(self, name, clazz):
        """
        Return a (possibly empty) list of all Java GATE resources with the given name and class name.

        Args:
            name: name of the resources
            clazz: the name of the java class the resource must be an instance of

        Returns:
            list of matching resources
        """
        return self.worker.getResources4Name(name, clazz)

    def loadDocumentFromFile(self, filename):
        """
        Load a Java GATE document from the given file name and return a handle to it.

        Args:
            filename: the file name/path of the Java GATE document to load.

        Returns:
            a handle to the Java GATE document
        """
        return self.worker.loadDocumentFromFile(filename)

    def loadDocumentFromFile4Mime(self, filename, mimetype):
        """
        Load a Java GATE document from the given file name, using the given mime type
        and return a handle to it.

        Args:
            filename: the file name/path of the Java GATE document to load.
            mimetype: the mimetype to use

        Returns:
            a handle to the Java GATE document
        """
        return self.worker.loadDocumentFromFile(filename, mimetype)

    def loadMavenPlugin(self, group, artifact, version):
        """
        Load the given Maven plugin into Java GATE.

        Args:
            group: group id of the plugin
            artifact:  artifact id of the plugin
            version: version of the plugin
        """
        self.worker.loadMavenPlugin(group, artifact, version)

    def loadPipelineFromFile(self, filename):
        """
        Load a pipeline/controller from the given file into Java GATE and return a CorpusController handle to it.

        Args:
            filename: the filename/path of the pipeline file

        Returns:
            a CorpusController handle to the loaded Java GATE pipeline
        """
        return self.worker.loadPipelineFromFile(filename)

    def loadPipelineFromPlugin(self, group, artifact, path):
        """
        Load a prepared pipeline from the given loaded GATE Mave plugin into Java GATE and return
        a CorpusController handle to it.

        Args:
            group: maven group id the plugin
            artifact: artifact id of the plugin
            path: path of the pipeline in the JAR

        Returns:
            a CorpusController handle to the pipeline
        """
        return self.worker.loadPipelineFromPlugin(group, artifact, path)

    def logActions(self, flag):
        """
        Enable/disable logging of actions carried out on the Java GATE side to the Java GATE logger.

        Args:
            flag: True to enable logging of actions
        """
        self.worker.logActions(flag)

    def newCorpus(self):
        """
        Create and return a handle to a new Java GATE corpus.

        Returns:
            handle to the Java GATE corpus
        """
        return self.worker.newCorpus()

    def pluginBuild(self):
        """
        Return the short commit id of the Python plugin on the Java GATE side.

        Returns:
            commit id of Python plugin
        """
        return self.worker.pluginBuild()


    def pluginVersion(self):
        """
        Return the version string of the Python plugin on the Java GATE side.

        Returns:
            version string of Python plugin
        """
        return self.worker.pluginVersion()

    def print2err(self, message):
        """
        Output the given message to System.err on the Java GATE side.

        Args:
            message: string to output
        """
        self.worker.print2err(message)


    def print2out(self, message):
        """
        Output the given message to System.out on the Java GATE side.

        Args:
            message: string to output
        """
        self.worker.print2out(message)

    def run4Corpus(self, pipeline, corpus):
        """
        Run the given Java GATE pipeline on the given Java GATE corpus.

        Args:
            pipeline: handle to a Java GATE pipeline
            corpus: handle to a Java GATE corpus
        """
        self.worker.run4Corpus(pipeline, corpus)

    def run4Document(self, pipeline, gdoc):
        """
        Run the given Java GATE pipeline on the given Java GATE document.

        Args:
            pipeline: handle to a Java GATE pipeline
            gdoc: handle to a Java GATE document
        """
        self.worker.run4Document(pipeline, gdoc)

    def runExcecutionFinished(self, pipeline):
        """
        Run the execution finished method for the given Java GATE pipeline.

        Args:
            pipeline: handle to a Java GATE pipeline
        """
        self.worker.runExecutionFinished(pipeline)

    def runExcecutionStarted(self, pipeline):
        """
        Run the execution started method for the given Java GATE pipeline.

        Args:
            pipeline: handle to a Java GATE pipeline
        """
        self.worker.runExecutionStarted(pipeline)

    def saveDocumentToFile(self, gdoc, filename, mimetype):
        """
        Save the Java GATE document to the given file, using the given mime type.
        At the moment this supports the GATE XML format (mimetype="") as well as
        formats supported by the FastInfoset  FormatBdoc plugins.

        Args:
            gdoc: handle to Java GATE document
            filename: name/path of the file to save to
            mimetype: the mime type to determine the format, "" for GATE XML
        """
        self.worker.saveDocumentToFile(gdoc, filename, mimetype)

    def pannsets2gannsets(self, annsets=None):
        """
        Convert from our convention to specifiy annotation sets and types to a Java list.
        This is necessary because py4j does not by default convert lists properly and also
        because our Java representation of the annsets specification has a different structure.
        The list returned from this is already a Java list!

        Args:
            annsets: annsets specification to convert

        Returns:
            java representation of the annsets specification (or None)
        """
        if annsets is None:
            return None
        # annsets is a python collection and cannot be passed directly to Java
        # see https://www.py4j.org/advanced_topics.html#collections-conversion
        from py4j.java_collections import ListConverter
        newannsets = []
        for spec in annsets:
            if isinstance(spec, str):
                plist = [spec, None]
            else:
                setname, types = spec
                if isinstance(types, str):
                    plist = [setname, types]
                else:
                    # types must be a list:
                    plist = [setname]
                    plist.extend(types)
            jlist = ListConverter().convert(plist, self.gateway._gateway_client)
            newannsets.append(jlist)
        jnewannsets = ListConverter().convert(newannsets, self.gateway._gateway_client)
        return jnewannsets

    def jsonAnnsets4Doc(self, gdoc, jannsets=None):
        """
        Return the JSON representation of the annotation sets in the GATE document, optionally
        filtered by the given annsets specification.

        The annsets specification should have the format as expected on the Java side: a list
        of lists of string. Each inner list has the set name to include as the first element
        and either null as the second element to include all types, or the types to include
        as the 2nd and subsequent elements.

        The method pannsets2gannsets(annsets) can be used to convert from our standard annset
        specification to the Java annsets specification.

        Args:
            gdoc: handle to Java GATE document
            jannsets: the annotation specification list as a Java list

        Returns:

        """
        return self.worker.jsonAnnsets4Doc(gdoc, jannsets)

    def showGui(self):
        """
        (CAUTION: EXPERIMENTAL) this shows the GATE GUI if we a re connected to a GATE process that runs without
        showing the GUI.
        """
        self.worker.showGui()


class GateWorkerAnnotator(Annotator):
    # TODO: something that starts a gate worker when created, loads pipeline in Java GATE,
    # sends over document
    # or document and selection of annotation sets/annotation types, runs pipeline,
    # and then fetches one or more annotation sets and updates the local document with them.
    # TODO: parameter to influence how exceptions are handled
    def __init__(
        self,
        pipeline,
        gatehome=None,
        port=25333,
        annsets_send=None,
        annsets_receive=None,
        replace_anns=False,
    ):
        """
        Create a GateWorker annotator.

        This starts the gate worker, loads the pipeline and
        can then be used to annotate Python gatenlp Document instances with the Java GATE
        pipeline.

        Note: to make sure that start/finish callbacks on the Java side are invoked, the annotator
        start() method should be invoked once before processing documents and finish() should
        get called once after processing documents. (Any Executor implementation shoudl do this
        autimatically)

        If the GateWorkerAnnotator is not used any more, close() should be invoked to terminate
        the Java GATE Worker process.

        Example:

            ```python
            pipeline = GateWorkerAnnotator("annie.xgapp")
            for idx, doc in enumerate(mycorpus):
                corpus[idx] = pipeline(doc)
            ```

        Args:
            pipeline: the path to a Java GATE pipeline to load into the GATE worker
            gatehome: the gate home directory to use, if not set, uses environment variable GATE_HOME
            port: the port to use (25333)
            annsets_send: a list of either annotation set names, or tuples where the first element
                is the name of an annotation set and the second element is either the name of a type
                or a list of type names. If not None, only the sets/types specified are sent to Java GATE.
                If an empty list is specified, no annotations are sent at all.
            annsets_receive: same format as annsets_send to specify which annotation sets/types are
                sent back to Python after the document has been processed on the Java side.
            replace_anns: if True and an annotation is received which already exists (same set and annotation id)
              then the existing annotation is replaced (if offsets and type are also same, only the features are
              replaced). If False, all received annotations are added which may change their annotation id.
        """
        self.pipeline = pipeline
        self.annsets_send = annsets_send
        self.annsets_receive = annsets_receive
        self.replace_anns = replace_anns
        self.gs = GateWorker(port=port, start=True, gatehome=gatehome)
        self.controller = self.gs.worker.loadPipelineFromFile(self.pipeline)
        self.corpus = self.gs.worker.newCorpus()
        self.controller.setCorpus(self.corpus)
        self.controller.setControllerCallbacksEnabled(False)

    def close(self):
        """
        Shut down the GateWorker used by this annotator.

        After calling this, the GateWorkerAnnotator instance cannot be used any more.
        """
        self.gs.close()

    def start(self):
        """
        Invoke the controller execution started method on the GATE controller.
        """
        self.controller.invokeControllerExecutionStarted()

    def finish(self):
        """
        Invoke the controller execution finished method on the GATE controller.
        """
        self.controller.invokeControllerExecutionFinished()

    def __call__(self, doc, **kwargs):
        """
        Run the GATE controller on the given document.

        This runs the GATE pipeline (controller) on the given document by first sending the document
        to the GATE process and coverting it to a GATE document there, running the pipeline on it,
        and sending the document back and converting back to a new gatenlp Document.

        Args:
            doc: the document to process
            **kwargs: ignored so far

        Returns:
            the processed gatenlp document
        """
        if self.annsets_send is not None:
            # create shallow copy, we only need it for reading!
            tmpdoc = doc.copy(annsets=self.annsets_send)
        else:
            tmpdoc = doc
        gdoc = self.gs.pdoc2gdoc(tmpdoc)
        self.gs.worker.run4Document(self.controller, gdoc)
        self.gs.gdocanns2pdoc(gdoc, doc, annsets=self.annsets_receive, replace=self.replace_anns)
        self.gs.del_resource(gdoc)
        return doc


def main():
    """
    Start a GATE worker from the command line.

    This is available as command `gatenlp-gate-worker`.
    Use option `--help` to get help about command line arguments.
    """
    ap = argparse.ArgumentParser(description="Start Java GATE Worker")
    ap.add_argument(
        "--download",
        action="store_true",
        help="Download GATE libraries to run GATE worker",
    )
    ap.add_argument("--port", default=25333, type=int, help="Port (25333)")
    ap.add_argument(
        "--host", default="127.0.0.1", type=str, help="Host to bind to (127.0.0.1)"
    )
    ap.add_argument(
        "--auth", default=None, type=str, help="Auth token to use (generate random)"
    )
    ap.add_argument("--noauth", action="store_true", help="Do not use auth token")
    ap.add_argument(
        "--gatehome",
        default=None,
        type=str,
        help="Location of GATE (environment variable GATE_HOME)",
    )
    ap.add_argument(
        "--platform",
        default=None,
        type=str,
        help="OS/Platform: windows or linux (autodetect)",
    )
    ap.add_argument(
        "--log_actions", action="store_true", help="If worker actions should be logged"
    )
    ap.add_argument(
        "--keep", action="store_true", help="Prevent shutting down the worker"
    )
    ap.add_argument("--debug", action="store_true", help="Show debug messages")
    args = ap.parse_args()
    if args.download:
        GateWorker.download()
    else:
        start_gate_worker(
            port=args.port,
            host=args.host,
            auth_token=args.auth,
            use_auth_token=not args.noauth,
            gatehome=args.gatehome,
            platform=args.platform,
            log_actions=args.log_actions,
            keep=args.keep,
            debug=args.debug,
        )


if __name__ == "__main__":
    main()
