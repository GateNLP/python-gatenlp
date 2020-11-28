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

# NOTE: we delay importing py4j to the class initializer. This allows us to make GateSlave available via gatenlp
# but does not force everyone to actually have py4j installed if they do not use the GateSlave
# from py4j.java_gateway import JavaGateway, GatewayParameters
from gatenlp import Document
from gatenlp.utils import init_logger
from gatenlp.processing.annotator import Annotator

JARVERSION = "1.0"

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

__pdoc__ = {"GateSlaveAnnotator.__call__": True}


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


def start_gate_slave(
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
    Run the gate slave program. This starts the Java program included with gatenlp to
    run GATE and execute the gate slave within GATE so that Python can connect to it.

    Args:
      port:  (Default value = 25333) Port number to use
      host:  (Default value = "127.0.0.1") Host address to bind to
      auth_token:  (Default value = None)  Authorization token to use. If None, creates a random token.
      use_auth_token:  (Default value = True) If False, do not aue an authorization token at all.
         This allows anyone who can connect to the host address to connect and use the gate slave process.
      java:  (Default value = "java") Java command (if on the binary path) or full path to the binary
         to use for running the gate slave program.
      platform:  (Default value = None) "win"/"windows" for Windows, anything else for non-Windows.
         If None, tries to determine automatically.
      gatehome:  (Default value = None) The path to where GATE is installed. If None, the environment
         variable "GATE_HOME" is used.
      log_actions:  (Default value = False) If True, the GATE Slave process will log everything it is
         ordered to do.
      keep:  (Default value = False) passed on to the gate slave process and tells the process if it should
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
        f"Starting gate slave, gatehome={gatehome}, auth_token={auth_token}, log_actions={log_actions}, keep={keep}"
    )
    jarloc = os.path.join(
        os.path.dirname(__file__), "_jars", f"gatetools-gatenlpslave-{JARVERSION}.jar"
    )
    if not os.path.exists(jarloc):
        raise Exception("Could not find jar, {} does not exist".format(jarloc))
    logger.debug(f"Using JAR: {jarloc}")
    cmdandparms = [java, "-cp"]
    cpsep = classpath_sep(platform=platform)
    cmdandparms.append(jarloc + cpsep + gate_classpath(gatehome, platform=platform))
    cmdandparms.append("gate.tools.gatenlpslave.GatenlpSlave")
    cmdandparms.append(str(port))
    cmdandparms.append(host)
    cmdandparms.append(log_actions)
    cmdandparms.append(keep)
    os.environ["GATENLP_SLAVE_TOKEN_" + str(port)] = auth_token
    cmd = " ".join(cmdandparms)
    logger.debug(f"Running command: {cmd}")
    subproc = subprocess.Popen(
        cmdandparms, stderr=subprocess.PIPE, bufsize=0, encoding="utf-8"
    )

    def shutdown():
        """
        Handler that gets invoked when the calling Python program exits.
        This terminates the gate slave by sending the SIGINT signal to it.
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
        if line == "PythonSlaveRunner.java: server start OK":
            break
        if line == "PythonSlaveRunner.java: server start NOT OK":
            raise Exception("Could not start server, giving up")
        print(line, file=sys.stderr)
    try:
        subproc.wait()
    except KeyboardInterrupt:
        print("Received keyboard interrupt, shutting down server...")
        shutdown()


class GateSlave:
    """
    Gate slave for remotely running arbitrary GATE and other JAVA operations in a separate
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
        Create an instance of the GateSlave and either start our own Java GATE process for it to use
        (start=True) or connect to an existing one (start=False).

        After the GateSlave instance has been create successfully, it is possible to:

        * Use one of the methods of the instance to perform operations on the Java side or exchange data

        * use GateSlave.slave to invoke methods from the PythonSlave class on the Java side

        * use GateSlave.jvm to directly construct objects or call instance or static methods

        NOTE: the GATE process must not output anything important/big to stderr because everything from
        stderr gets captured and used for communication between the Java and Python processes. At least
        part of the output to stderr may only be passed on after the GATE process has ended.

        Example:

            ```python
            gs = GateSlave()
            pipeline = gs.slave.loadPipelineFromFile("thePipeline.xgapp")
            doc = gs.slave.createDocument("Some document text")
            gs.slave.run4doc(pipeline,doc)
            pdoc = gs.gdoc2pdoc(doc)
            gs.slave.deleteResource(doc)
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
        log_actions: if the gate slave should log the actions it is doing
        keep: normally if gs.close() is called and we are not connected to the PythonSlaveLr,
               the slave will be shut down. If this is True, the gs.close() method does not shut down
               the slave.
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
        self.slave = None
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
                f"gatetools-gatenlpslave-{JARVERSION}.jar",
            )
            if not os.path.exists(jarloc):
                raise Exception("Could not find jar, {} does not exist".format(jarloc))
            cmdandparms = [java, "-cp"]
            cpsep = classpath_sep(platform=platform)
            cmdandparms.append(
                jarloc + cpsep + gate_classpath(self.gatehome, platform=platform)
            )
            cmdandparms.append("gate.tools.gatenlpslave.GatenlpSlave")
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
            os.environ["GATENLP_SLAVE_TOKEN_" + str(self.port)] = self.auth_token
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
                if line == "PythonSlaveRunner.java: server start OK":
                    break
                if line == "PythonSlaveRunner.java: server start NOT OK":
                    raise Exception("Could not start server, giving up")
                print(line, file=sys.stderr)
            atexit.register(self.close)
        self.gateway = JavaGateway(
            gateway_parameters=GatewayParameters(port=port, auth_token=self.auth_token)
        )
        self.jvm = self.gateway.jvm
        self.slave = self.gateway.entry_point
        self.gate_version = self.jvm.gate.Main.version
        self.gate_build = self.jvm.gate.Main.build
        self.slave_version = self.slave.pluginVersion()
        self.slave_build = self.slave.pluginBuild()

    @staticmethod
    def download():
        """
        Download GATE libraries into a standard location so we can run the GATE slave even if GATE_HOME
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
        Clean up: if the gate slave process was started by us, we will shut it down.
        Otherwise we can still close it if it was started by the slaverunner, not the Lr
        Note: if it was started by us, it was started via the slaverunner.
        """
        if not self.closed and self.slave.isClosable():
            self.closed = True
            self.gateway.shutdown()
            if self.gateprocess is not None:
                for line in self.gateprocess.stderr:
                    print(line, file=sys.stderr, end="")
                self.gateprocess.wait()

    def log_actions(self, onoff):
        """
        Swith logging actions at the slave on or off.

        Args:
          onoff: True to log actions, False to not log them
        """
        self.slave.logActions(onoff)

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
        return self.slave.loadDocumentFromFile(path, mimetype)

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
        self.slave.saveDocumentToFile(path, mimetype)

    def gdoc2pdoc(self, gdoc):
        """
        Convert the GATE document to a python document and return it.

        Args:
          gdoc: the handle to a GATE document

        Returns:
          a gatenlp Document instance
        """
        bjs = self.slave.getBdocJson(gdoc)
        return Document.load_mem(bjs, fmt="bdocjs")

    def pdoc2gdoc(self, pdoc):
        """
        Convert the Python gatenlp document to a GATE document and return a handle to it.

        Args:
          pdoc: python gatenlp Document

        Returns:
          handle to GATE document
        """
        json = pdoc.save_mem(fmt="bdocjs")
        return self.slave.getDocument4BdocJson(json)

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
        when closing down the GATE slave.
        """
        self.slave.showGui()


class GateSlaveAnnotator(Annotator):
    # TODO: something that starts a gate slave when created, loads pipeline in Java GATE,
    # sends over document
    # or document and selection of annotation sets/annotation types, runs pipeline,
    # and then fetches one or more annotation sets and updates the local document with them.
    # TODO: parameter to influence how exceptions are handled
    def __init__(self, pipeline, gatehome=None, port=25333, sets_send=None, sets_receive=None, replace_anns=False):
        """
        Create a GateSlave annotator.

        This starts the gate slave, loads the pipeline and
        can then be used to annotate Python gatenlp Document instances with the Java GATE
        pipeline.

        Note: to make sure tha start/finish callbacks on the Java side are invoked, the annotator
        start() method should be invoked once before processing documents and finish() should
        get called once after processing documents.

        If the GateSlaveAnnotator is not used any more, close() should be invoked to terminate
        the Java GATE Slave process.

        Example:

            ```python
            pipeline = GateSlaveAnnotator("annie.xgapp")
            for idx, doc in enumerate(mycorpus):
                corpus[idx] = pipeline(doc)
            ```

        Args:
            pipeline: the path to a Java GATE pipeline to load into the GATE slave
            gatehome: the gate home directory to use, if not set, uses environment variable GATE_HOME
            port: the port to use (25333)
            sets_send: a dictionary where the keys are the name of the target annotation set at the
              Java side and the values are either the source annotation set name or a list of
              tuples of the form (setname, typename).
            sets_receive: a dictionary where the keys are the name of the target annotation set at the
              Python side and the values are either the source annotation set name in Java or ta list
              of tuples of the form (setname, typename).
            replace_anns (default: False) if True, existing annotations (in the sets, of the types
              specified in sets_receive or all) are removed before the retrieved annotations are added.
              In this case, the annotation ids of the retrieved annotations are kept.
              If False, the retrieved annotations are added to the existing sets and may get new, different
              annotation ids.
        """
        self.pipeline = pipeline
        if sets_send is not None or sets_receive is not None:
            raise NotImplemented
        self.sets_send = sets_send
        self.sets_receive = sets_receive
        self.gs = GateSlave(port=port, start=True, gatehome=gatehome)
        self.controller = self.gs.slave.loadPipelineFromFile(self.pipeline)
        self.corpus = self.gs.slave.newCorpus()
        self.controller.setCorpus(self.corpus)
        self.controller.setControllerCallbacksEnabled(False)

    def close(self):
        """
        Shut down the GateSlave used by this annotator.

        After calling this, the GateSlaveAnnotator instance cannot be used any more.
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

        IMPORTANT: the exact way of how the final document that gets returned by this method is created
        may change or depend on how the annotator is configured: it may or may not be the original document
        which gets modified in place or new document with the original document unchanged.

        Args:
            doc: the document to process
            **kwargs: ignored so far

        Returns:
            the processed gatenlp document which may be the original one passed to this method
            or a new one.
        """
        # TODO: how to handle exceptions?
        if self.sets_send is not None:
            # TODO: create the json for the pdoc restricted to these sets, and with setnames renamed
            # TODO: then send the document as JSON directly
            pass
        # TODO: LIMIT the sets to send by directly sending the JSON using
        # TODO: doc.save_mem(fmt="json", annsets=["set",  ("set2", ["Type1", "Type2"])])
        gdoc = self.gs.pdoc2gdoc(doc)
        self.gs.slave.run4Document(self.controller, gdoc)
        if self.sets_receive is not None:
            # TODO: retrieve the JSON limited to just the specified sets
            pass
        else:
            # TODO: retrieve the JSON for all sets
            # NOTE: for now we always retrieve back the whole annotated document
            doc = self.gs.gdoc2pdoc(gdoc)
        # TODO: once we have the set or sets, add them to the existing python document
        # TODO: as specified via the sets_receive and replace_anns parameters
        self.gs.del_resource(gdoc)
        return doc


def main():
    """
    Start a GATE slave from the command line.

    This is available as command `gatenlp-gate-slave`.
    Use option `--help` to get help about command line arguments.
    """
    ap = argparse.ArgumentParser(description="Start Java GATE Slave")
    ap.add_argument(
        "--download",
        action="store_true",
        help="Download GATE libraries to run GATE slave",
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
        "--log_actions", action="store_true", help="If slave actions should be logged"
    )
    ap.add_argument(
        "--keep", action="store_true", help="Prevent shutting down the slave"
    )
    ap.add_argument("--debug", action="store_true", help="Show debug messages")
    args = ap.parse_args()
    if args.download:
        GateSlave.download()
    else:
        start_gate_slave(
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
