#!/usr/bin/env python
"""
Module for interacting with a Java GATE process.
"""
import socket

import py4j
from py4j.java_gateway import JavaGateway
from typing import Optional, List, Tuple, Union
import sys
import subprocess
import os
import pathlib
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

JARVERSION = "1.0"

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def jar_loc() -> str:
    """Return the path to the gate worker jar as a string."""
    return str(pathlib.Path(__file__).parent.parent.
               joinpath("_jars").joinpath(f"gatetools-gatenlpworker-{JARVERSION}.jar"))


def classpath_sep(platform: Optional[str] = None) -> str:  # pragma: no cover
    """
    Get the system-specific classpath separator character.

    Args:
      platform:  (Default value = None) "win" or "windows" for Windows, anything else for non-windows
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


def gate_classpath(gatehome: str, platform: Optional[str] = None) -> str:  # pragma: no cover
    """
    Return the GATE classpath components as a string, with the path seperator characters appropriate
    for the operating system.

    Args:
      gatehome: path where GATE is installed, either as a cloned git repo or a downloaded installation dir.
      platform:  (Default value = None) "win" or "windows" for Windows, anything else for non-Windows.

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
        with open(cpfile, "rt", encoding="utf-8") as infp:
            c_p = infp.read()
            return c_p + cpsep + bindir
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
        port: int = 25333,
        host: str = "127.0.0.1",
        auth_token: Optional[str] = None,
        use_auth_token: bool = True,
        java: str = "java",
        platform: Optional[str] = None,
        gatehome: Optional[str] = None,
        log_actions: bool = False,
        keep: bool = False,
        debug: bool = False,
):   # pragma: no cover
    """
    Run the gate worker program. This starts the Java program included with gatenlp to
    run GATE and execute the gate worker within GATE so that Python can connect to it.

    This methods waits for the subprocess to end.

    Args:
        port:  (Default value = 25333) Port number to use
        host:  (Default value = "127.0.0.1") Host address to bind to
        auth_token:  (Default value = None)  Authorization token to use. If None, creates a random token.
        use_auth_token:  (Default value = True) If False, do not aue an authorization token at all.
           This allows anyone who can connect to the host address to connect and use the gate worker process.
        java:  (Default value = "java") Java command (if on the binary path) or full path to the binary
           to use for running the gate worker program.
        platform:  (Default value = None) "win" or "windows" for Windows, anything else for non-Windows.
           If None, tries to determine automatically.
        gatehome:  (Default value = None) The path to where GATE is installed. If None, the environment
           variable "GATE_HOME" is used.
        log_actions:  (Default value = False) If True, the GATE Worker process will log everything it is
           ordered to do.
        keep:  (Default value = False) passed on to the gate worker process and tells the process if it should
           report to the using Python process that it can be closed or not.
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
    jarloc = jar_loc()
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
    logger.info(f"Running as process with PID {subproc.pid}")

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

# pylint: disable=C0103


def check_port_used(host: str, port: int) -> bool:
    """
    Check if the given port on the given host is in use.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn = sock.connect_ex((host, port))
    used = False
    if conn == 0:
        used = True
    sock.close()
    return used


class GateWorker:
    """
    Gate worker for remotely running arbitrary GATE and other JAVA operations in a separate
    Java GATE process.
    """

    def __init__(
            self,
            port: int = 25333,
            retry_ports: int = 10,
            start: bool = True,
            java: str = "java",
            host: str = "127.0.0.1",
            gatehome: Optional[str] = None,
            platform: Optional[str] = None,
            auth_token: Optional[str] = None,
            use_auth_token: bool = True,
            log_actions: bool = False,
            keep: bool = False,
            debug: bool = False,
            ):
        """
        Create an instance of the GateWorker and either start our own Java GATE process for it to use
        (start=True) or connect to an existing one (start=False).

        After the GateWorker instance has been create successfully, it is possible to:

        * Use one of the methods of the instance to perform operations on the Java side or exchange data

        * use GateWorker.worker to invoke methods from the PythonWorker class on the Java side (but for most of these
          method there is a shortcut implementation directly on GateWorker which should be preferred!)

        * use GateWorker.jvm to directly construct objects or call instance or static methods

        NOTE: the GATE process must not output anything important/big to stderr because everything from
        stderr gets captured and used for communication between the Java and Python processes. At least
        part of the output to stderr may only be passed on after the GATE process has ended.

        Example:

            ```python
            gw = GateWorker()
            pipeline = gw.loadPipelineFromFile("thePipeline.xgapp")
            doc = gw.createDocument("Some document text")
            gw.worker.run4Document(pipeline,doc)
            pdoc = gw.gdoc2pdoc(doc)
            gw.deleteResource(doc)
            # process the document pdoc ...
            ```

        port: port to use
        retry_ports: if start=True and the specified port is in use, try this many
            additional ports before giving up (default: 10) Note: this uses a simple implementation which checks
            in advance if the port is in use; this strategy may fail in cases where a port that was found to be
            free is getting used in the short time between the check and the actual use by the gate worker.
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
        if debug:
            self.logger = init_logger("GateWorker", lvl="DEBUG")
        else:
            self.logger = init_logger("GateWorker")

        from py4j.java_gateway import JavaGateway, GatewayParameters

        self._gatehome = gatehome
        self._port = port
        self._host = host
        self._platform = platform
        self._gateprocess = None
        self._gateway = None
        self._closed = False
        if use_auth_token:
            if not auth_token:
                self._auth_token = secrets.token_urlsafe(20)
            else:
                self._auth_token = auth_token
        else:
            self._auth_token = ""
        if gatehome is None and start:
            gatehome = os.environ.get("GATE_HOME")
            if gatehome is None:
                raise Exception(
                    "Parameter gatehome is None and environment var GATE_HOME not set"
                )
            self._gatehome = gatehome
        if start:
            # make sure we find the jar we need
            # logger.info("DEBUG: file location: {}".format(__file__))
            used = True
            if retry_ports:
                for i in range(retry_ports):
                    port = self.port + i
                    used = check_port_used(self.host, port)
                    if not used:
                        self._port = port
                        break
                    logger.info(f"Port {port} is already in use")
                if used:
                    raise Exception(f"Port(s) in use: {self.port} to {port}")
            jarloc = jar_loc()
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
            os.environ["GATENLP_WORKER_TOKEN_" + str(self.port)] = self._auth_token
            cmd = " ".join(cmdandparms)
            self.logger.debug(f"Running command: {cmd}")
            subproc = subprocess.Popen(
                cmdandparms, stderr=subprocess.PIPE, bufsize=0, encoding="utf-8"
            )
            self._gateprocess = subproc
            haveerror = False
            while True:
                # NOTE: the following line can block when the subprocess ends with an error
                line = subproc.stderr.readline()
                if line == "":
                    break
                line = line.rstrip("\n\r")
                if line == "PythonWorkerRunner.java: server start OK":
                    break
                if line == "PythonWorkerRunner.java: server start NOT OK":
                    haveerror = True
                    # if we get an error we continue to loop through stderr until we get end of stream (line=="")
                    # and only raise the exception after the loop.
                if line.startswith("Java GatenlpWorker ENDING"):
                    break
                print(line, file=sys.stderr)
            if haveerror:
                raise Exception("Error when starting server")
            atexit.register(self.close)
        self._gateway = JavaGateway(
            gateway_parameters=GatewayParameters(port=port, auth_token=self._auth_token)
        )
        # do not wait until the gateway is used by the user to detect a problem, instead, retrieve the GATE
        # version here to check basic functionality
        _ = self.gate_version

    def __repr__(self):
        return f"Gateworker(port={self.port},host={self.host},gate_home={self.gatehome})"

    @property
    def jvm(self) -> py4j.java_gateway.JVMView:
        """
        Returns the JVM instance which allows to interact with Java.

        Returns:
            The JVMView instance

        """
        return self.gateway.jvm

    @property
    def worker(self) -> py4j.java_gateway.JavaObject:
        """
        A JavaObject which provides the methods on the Java side.

        Returns:
            The worker JavaObject

        """
        return self.gateway.entry_point

    @property
    def gate_version(self) -> str:
        """
        Return the GATE version of the connected GATE process.
        """
        return self.jvm.gate.Main.version

    @property
    def gate_build(self) -> str:
        """
        Return the GATE build id of the connected GATE process.
        """
        return self.jvm.gate.Main.build

    @property
    def worker_version(self) -> str:
        """
        Return the Gate Worker version of the connected GATE process.
        """
        return self.worker.pluginVersion()

    @property
    def worker_build(self) -> str:
        """
        Return the build id of the Worker of the connected GATE proces..
        """
        return self.worker.pluginBuild()

    @property
    def gatehome(self) -> str:
        """
        Return the GATE home path of the connected GATE process as a string.
        """
        return self._gatehome

    @property
    def port(self) -> int:
        """
        Return the port of the connected GATE process as an int.
        """
        return self._port

    @property
    def host(self) -> str:
        """
        Return the host name or address of the connected GATE process as a str.
        """
        return self._host

    @property
    def platform(self) -> Optional[str]:
        return self._platform

    @property
    def gateprocess(self) -> subprocess.Popen:
        """
        Get the process.

        Returns:
            A subprocess.Popen object.
            See https://docs.python.org/3/library/subprocess.html#popen-objects for methods
            that can be used on this object.

        """
        return self._gateprocess

    @property
    def getpid(self) -> Optional[int]:
        """
        Get the process id (or None if no process).

        Returns:
            Process ID (int)

        """
        proc = self.gateprocess
        if proc:
            return proc.pid

    @property
    def gateway(self) -> py4j.java_gateway.JavaGateway:
        """
        Return the py4j JavaGateway instance. This object provides the method
        help(jvm.some.object) for getting help about known Java objects.
        """
        return self._gateway

    # @staticmethod
    # def download():
    #     """
    #     Download GATE libraries into a standard location so we can run the GATE worker even if GATE_HOME
    #     is not set.
    #
    #     NOTE YET IMPLEMENTED.
    #     """
    #     # TODO: this should use the command and bootstrapping jar in gate-downloader:
    #     # copy the whole directory into the standard per-user config directory for the system
    #     # run the command
    #     # use the generated gate.classpath as for a compiled local git repo
    #     # NOTE: should change error message if GATE_HOME is not set to hint at this!
    #     # (option --downlaod for the script)
    #     # NOTE: add to documentation
    #     raise Exception("Not yet implemented")

    def close(self):
        """
        Clean up: if the gate worker process was started by us, we will shut it down.
        Otherwise we can still close it if it was started by the workerrunner, not the Lr
        Note: if it was started by us, it was started via the workerrunner.
        """
        if not self._closed and self.worker.isClosable():
            self._closed = True
            self.gateway.shutdown()
            if self.gateprocess is not None:
                for line in self.gateprocess.stderr:
                    print(line, file=sys.stderr, end="")
                self.gateprocess.wait()

    def __enter__(self):
        return self

    def __exit__(self, _exptype, _value, _traceback):
        self.close()

    def log_actions(self, onoff: bool):
        """
        Switch logging actions at the worker on or off.

        Args:
          onoff: True to log actions, False to not log them
        """
        self.worker.logActions(onoff)

    def load_gdoc(self, path: str, mimetype: Optional[str] = None) -> py4j.java_gateway.JavaObject:
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

    def save_gdoc(self,
                  gdoc: py4j.java_gateway.JavaObject,
                  path: str,
                  mimetype: Optional[str] = None,
                  inline_anntypes: Optional[List[str]] = None,
                  inline_annset: Optional[str] = "",
                  inline_features: Optional[bool] = True):
        """
        Save GATE document to the given path.

        Args:
          gdoc: GATE document handle
          path: destination path
          mimetype: mimtetype, only the following types are allowed: ""/None: GATE XML,
                application/fastinfoset, text/xml for inline XML, 
                and all mimetypes supported by the
                Format_Bdoc plugin. (Default value = None). 
          inline_anntypes: annotation types for inline XML export. Only works with mimetype xml.
                If None, all types in the inline_annset are exported, if a list, only the 
                types in the list are exported.
          inline_annset: annotation set for inline XML export.
          inline_features: save features as attribute for inline XML export.
        """
        if mimetype is None:
            mimetype = ""
        self.worker.saveDocumentToFile(gdoc, path, mimetype, self.panntype2ganntype(inline_anntypes), inline_annset, inline_features)

    def gdoc2pdoc(self, gdoc: py4j.java_gateway.JavaObject) -> Document:
        """
        Convert the GATE document to a python document and return it.

        Args:
          gdoc: the handle to a GATE document

        Returns:
          a gatenlp Document instance
        """
        bjs = self.worker.getBdocJson(gdoc)
        return Document.load_mem(bjs, fmt="bdocjs")

    def pdoc2gdoc(self, pdoc: Document, annspec: Optional[List[Tuple]] = None) -> py4j.java_gateway.JavaObject:
        """
        Convert the Python gatenlp document to a GATE document and return a handle to it.

        Args:
            pdoc: python gatenlp Document
            annspec: a list of either set names, or tuples where the first element is a set name and the
                second element is either a type name or a list of type names.

        Returns:
            handle to GATE document
        """
        jsondata = pdoc.save_mem(fmt="bdocjs", annspec=annspec)
        return self.worker.getDocument4BdocJson(jsondata)

    def gdocanns2pdoc(self, gdoc: py4j.java_gateway.JavaObject, pdoc: Document,
                      annspec: Optional[List[Tuple]] = None, replace: bool = False) -> Document:
        """
        Retrieve the annotations from the GATE document and add them to the python gatenlp document.
        This modifies the pdoc in place and returns it.

        Args:
            gdoc: a handle to a Java GATE document
            pdoc: Python gatenlp document
            annspec: if not None, an annotation specification: a list of set names or tuples where the first
                element is a set name and the second element is either a type name or a list of type names
            replace: if True, replaces all annotations with the same set and annotation id, otherwise adds
                annotaitons with potentially a new annotation id.

        Returns:
            the modified pdoc
        """
        # to make it easier on the Java side to interpret the annotation specification, convert it so that
        # all elements are a list where first element is always the set name and all remaining elements
        # are tyepe names. If there is one remaining element which is null, include all types for that set.
        newannspec = self.pannspec2gannspec(annspec)
        # now retrieve the BDOC JSON representation of the annotations
        thejson = self.jsonAnnsets4Doc(gdoc, newannspec)
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

    def load_pdoc(self, path: str, mimetype: Optional[str] = None) -> Document:
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

    def del_resource(self, resource: py4j.java_gateway.JavaObject):
        """
        DEPRECATED: please use deleteResource(resource) instead!

        Delete/unload a GATE resource (Document, Corpus, ProcessingResource etc) from GATE.

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
    def createDocument(self, content: str) -> py4j.java_gateway.JavaObject:
        """
        Create a Java GATE document from the content string and return a handle to it.

        Args:
            content: the text of the document

        Returns:
            handle to Java GATE document
        """
        return self.worker.createDocument(content)

    def deleteResource(self, resource: py4j.java_gateway.JavaObject):
        """
        Delete/unload a Java GATE resource (Document, Corpus, ProcessingResource etc) from GATE.
        This is particularly important to do when processing a large number of documents for each document
        that is finished processing, otherwise the documents
        will accumulate in the Java process and eat up all memory. NOTE: just removing all references to a
        GATE document does not delete/unload the document!

        Args:
            resource: a handle to some Java GATE resource
        """
        self.worker.deleteResource(resource)

    def findMavenPlugin(self, group: str, artifact: str) -> py4j.java_gateway.JavaObject:
        """
        Find a Java GATE Maven plugin and return a handle to it, or None if nothing found.

        Args:
            group: the Maven group for the plugin
            artifact: the artifact name for the plugin

        Returns:
            a handle to the plugin or None if not found
        """
        return self.worker.findMavenPlugin(group, artifact)

    def getBdocJson(self, gdoc: py4j.java_gateway.JavaObject) -> str:
        """
        Return the Bdoc JSON serialization of a Java GATE document as string.

        Args:
            gdoc: a handle to a GATE document

        Returns:
            BDOC serialization JSON string
        """
        return self.worker.getBdocJson(gdoc)

    def getCorpus4Name(self, name: str) -> py4j.java_gateway.JavaObject:
        """
        Return a handle to the first Java GATE corpus with the given name or None if none found.

        Args:
            name: corpus name

        Returns:
            first matching corpus or None
        """
        return self.worker.getCorpus4Name(name)

    def getCorpusNames(self) -> List[str]:
        """
        Return a list of all Java GATE corpus names known.

        Returns:
            list of corpus names
        """
        return self.worker.getCorpusNames()

    def getDocument4BdocJson(self, bdocjson: str) -> py4j.java_gateway.JavaObject:
        """
        Returns a handle to a Java GATE document created from the Bdoc JSON string.

        Args:
            bdocjson: a BDOC JSON string

        Returns:
            handle to the Java GATE document
        """
        return self.worker.getDocument4BdocJson(bdocjson)

    def getDocument4Name(self, name: str) -> py4j.java_gateway.JavaObject:
        """
        Return a handle to the first Java GATE document that has the given name or None if none found.

        Args:
            name: the document name

        Returns:
            a handle to the Java GATE document
        """
        return self.worker.getDocument4Name(name)

    def getDocumentNames(self) -> List[str]:
        """
        Return a list of known Java GATE document names.

        Returns:
            list of Java GATE document names
        """
        return self.worker.getDocumentNames()

    def getPipeline4Name(self, name: str) -> py4j.java_gateway.JavaObject:
        """
        Return a handle to the first Java GATE pipeline/controller that has the given name or
        None if none found.

        Args:
            name: name of the pipeline

        Returns:
            handle to the pipeline
        """
        return self.worker.getPipeline4Name(name)

    def getPipelineNames(self) -> List[str]:
        """
        Return a list of all know Java GATE pipeline names.

        Returns:
            list of pipeline names
        """
        return self.worker.getPipelineNames()

    def getPr4Name(self, name: str) -> py4j.java_gateway.JavaObject:
        """
        Return a handle to the first Java GATE processing resource that has the given name
        or None if none found.

        Args:
            name: the name of the processing resource

        Returns:
            a handle to the processing resource or None
        """
        return self.worker.getPr4Name(name)

    def getPrNames(self) -> List[str]:
        """
        Return a list of known Java GATE  processing resource names.

        Returns:
            list of PR names
        """
        return self.worker.getPrNames()

    def getResources4Name(self, name: str) -> py4j.java_gateway.JavaObject:
        """
        Return a (possibly empty) list of all Java GATE resources with the given name.

        Args:
            name: name of the resources

        Returns:
            list of matching resources
        """
        return self.worker.getResources4Name(name)

    def getResources4NameClass(self, name: str, clazz: str) -> List[py4j.java_gateway.JavaObject]:
        """
        Return a (possibly empty) list of all Java GATE resources with the given name and class name.

        Args:
            name: name of the resources
            clazz: the name of the java class the resource must be an instance of

        Returns:
            list of matching resources
        """
        return self.worker.getResources4Name(name, clazz)

    def loadDocumentFromFile(self, filename: str) -> py4j.java_gateway.JavaObject:
        """
        Load a Java GATE document from the given file name and return a handle to it.

        Args:
            filename: the file name/path of the Java GATE document to load.

        Returns:
            a handle to the Java GATE document
        """
        return self.worker.loadDocumentFromFile(filename)

    def loadDocumentFromFile4Mime(self, filename: str, mimetype: str) -> py4j.java_gateway.JavaObject:
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

    def loadMavenPlugin(self, group: str, artifact: str, version: str):
        """
        Load the given Maven plugin into Java GATE.

        Args:
            group: group id of the plugin
            artifact:  artifact id of the plugin
            version: version of the plugin
        """
        self.worker.loadMavenPlugin(group, artifact, version)

    def loadPipelineFromFile(self, filename: str) -> py4j.java_gateway.JavaObject:
        """
        Load a pipeline/controller from the given file into Java GATE and return a CorpusController handle to it.

        Args:
            filename: the filename/path of the pipeline file

        Returns:
            a CorpusController handle to the loaded Java GATE pipeline
        """
        return self.worker.loadPipelineFromFile(filename)

    def loadPipelineFromUri(self, uri: str) -> py4j.java_gateway.JavaObject:
        """
        Load a pipeline/controller from the given uri into Java GATE and return a CorpusController handle to it.

        Args:
            uri: the uri of the pipeline file

        Returns:
            a CorpusController handle to the loaded Java GATE pipeline
        """
        return self.worker.loadPipelineFromUri(uri)

    def loadPipelineFromPlugin(self, group: str, artifact: str, path: str) -> py4j.java_gateway.JavaObject:
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

    def logActions(self, flag: bool):
        """
        Enable/disable logging of actions carried out on the Java GATE side to the Java GATE logger.

        Args:
            flag: True to enable logging of actions
        """
        self.worker.logActions(flag)

    def newCorpus(self) -> py4j.java_gateway.JavaObject:
        """
        Create and return a handle to a new Java GATE corpus.

        Returns:
            handle to the Java GATE corpus
        """
        return self.worker.newCorpus()

    def pluginBuild(self) -> str:
        """
        Return the short commit id of the Python plugin on the Java GATE side.

        Returns:
            commit id of Python plugin
        """
        return self.worker.pluginBuild()

    def pluginVersion(self) -> str:
        """
        Return the version string of the Python plugin on the Java GATE side.

        Returns:
            version string of Python plugin
        """
        return self.worker.pluginVersion()

    def print2err(self, message: str):
        """
        Output the given message to System.err on the Java GATE side.

        Args:
            message: string to output
        """
        self.worker.print2err(message)

    def print2out(self, message: str):
        """
        Output the given message to System.out on the Java GATE side.

        Args:
            message: string to output
        """
        self.worker.print2out(message)

    def run4Corpus(self, pipeline: py4j.java_gateway.JavaObject, corpus: py4j.java_gateway.JavaObject):
        """
        Run the given Java GATE pipeline on the given Java GATE corpus.

        Args:
            pipeline: handle to a Java GATE pipeline
            corpus: handle to a Java GATE corpus
        """
        self.worker.run4Corpus(pipeline, corpus)

    def run4Document(self, pipeline: py4j.java_gateway.JavaObject, gdoc: py4j.java_gateway.JavaObject):
        """
        Run the given Java GATE pipeline on the given Java GATE document.

        Args:
            pipeline: handle to a Java GATE pipeline
            gdoc: handle to a Java GATE document
        """
        self.worker.run4Document(pipeline, gdoc)

    def runExcecutionFinished(self, pipeline: py4j.java_gateway.JavaObject):
        """
        Run the execution finished method for the given Java GATE pipeline.

        Args:
            pipeline: handle to a Java GATE pipeline
        """
        self.worker.runExecutionFinished(pipeline)

    def runExcecutionStarted(self, pipeline: py4j.java_gateway.JavaObject):
        """
        Run the execution started method for the given Java GATE pipeline.

        Args:
            pipeline: handle to a Java GATE pipeline
        """
        self.worker.runExecutionStarted(pipeline)

    def saveDocumentToFile(self,
                           gdoc: py4j.java_gateway.JavaObject,
                           filename: str,
                           mimetype: str="",
                           inline_anntypes: Optional[List[str]]=None,
                           inline_annset: str="",
                           inline_features: bool=True):
        """
        Save the Java GATE document to the given file, using the given mime type.
        At the moment this supports the GATE XML format (mimetype="") as well as
        formats supported by the FastInfoset  FormatBdoc plugins.

        Args:
            gdoc: handle to Java GATE document
            filename: name/path of the file to save to
            mimetype: the mime type to determine the format, "" for GATE XML, text/xml for GATE inline XML
            inline_anntypes: annotation types for inline XML export.
            inline_annset: annotation set name.
            inline_features: save features as attributes.
        """
        self.worker.saveDocumentToFile(gdoc, filename, mimetype, self.panntype2ganntype(inline_anntypes), inline_annset, inline_features)

    def pannspec2gannspec(self,
                          annspec: Union[str, List[Union[str, Tuple]]]=None) -> Optional[py4j.java_gateway.JavaObject]:
        """
        Convert from our convention to specifiy annotation sets and types to a Java list.
        This is necessary because py4j does not by default convert lists properly and also
        because our Java representation of the annspec specification has a different structure.
        The list returned from this is already a Java list!

        Args:
            annspec: annotation specification to convert

        Returns:
            java representation of the annotation specification (or None)
        """
        if annspec is None:
            return None
        # annspec is a python collection and cannot be passed directly to Java
        # see https://www.py4j.org/advanced_topics.html#collections-conversion
        from py4j.java_collections import ListConverter
        if isinstance(annspec, str):
            annspec = [annspec]
        newannspec = []
        for spec in annspec:
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
            newannspec.append(jlist)
        jnewannspec = ListConverter().convert(newannspec, self.gateway._gateway_client)
        return jnewannspec

    def panntype2ganntype(self, inline_anntypes: List[str]) -> Optional[py4j.java_gateway.JavaObject]:
        """
        Convert annotations types string list to a Java list.
        """
        if inline_anntypes is None:
            return None
        # annspec is a python collection and cannot be passed directly to Java
        # see https://www.py4j.org/advanced_topics.html#collections-conversion
        from py4j.java_collections import ListConverter
        return ListConverter().convert(inline_anntypes, self.gateway._gateway_client)

    def jsonAnnsets4Doc(self,
                        gdoc: py4j.java_gateway.JavaObject,
                        jannspec: py4j.java_gateway.JavaObject) -> str:
        """
        Return the JSON representation of the annotation sets in the GATE document, optionally
        filtered by the given annotation specification.

        The jannspec specification should have the format as expected on the Java side: a list
        of lists of string. Each inner list has the set name to include as the first element
        and either null as the second element to include all types, or the types to include
        as the 2nd and subsequent elements.

        The method pannspec2gannspec(annspec) can be used to convert from our standard annotation
        specification to the Java annotation specification.

        Args:
            gdoc: handle to Java GATE document
            jannspec: the annotation specification list as a Java list

        Returns:
            JSON string
        """
        return self.worker.jsonAnnsets4Doc(gdoc, jannspec)

    def showGui(self):
        """
        (CAUTION: EXPERIMENTAL) this shows the GATE GUI if we a re connected to a GATE process that runs without
        showing the GUI.
        """
        self.worker.showGui()


def run_gate_worker():   # pragma: no cover
    """
    Start a GATE worker from the command line.

    This is available as command `gatenlp-gate-worker`.
    Use option `--help` to get help about command line arguments.
    """
    argparser = argparse.ArgumentParser(description="Start Java GATE Worker")
    argparser.add_argument(
        "--download",
        action="store_true",
        help="Download GATE libraries to run GATE worker",
    )
    argparser.add_argument("--port", default=25333, type=int, help="Port (25333)")
    argparser.add_argument(
        "--host", default="127.0.0.1", type=str, help="Host to bind to (127.0.0.1)"
    )
    argparser.add_argument(
        "--auth", default=None, type=str, help="Auth token to use (generate random)"
    )
    argparser.add_argument("--noauth", action="store_true", help="Do not use auth token")
    argparser.add_argument(
        "--gatehome",
        default=None,
        type=str,
        help="Location of GATE (environment variable GATE_HOME)",
    )
    argparser.add_argument(
        "--platform",
        default=None,
        type=str,
        help="OS/Platform: windows or linux (autodetect)",
    )
    argparser.add_argument(
        "--log_actions", action="store_true", help="If worker actions should be logged"
    )
    argparser.add_argument(
        "--keep", action="store_true", help="Prevent shutting down the worker"
    )
    argparser.add_argument("--debug", action="store_true", help="Show debug messages")
    args = argparser.parse_args()
    if args.download:
        raise Exception("--download not implemented yet ")
    #subprocess =
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
    #logger.info(f"Running with PID {subprocess.pid}")


if __name__ == "__main__":   # pragma: no cover
    run_gate_worker()
