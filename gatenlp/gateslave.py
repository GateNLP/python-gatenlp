#!/usr/bin/env python
"""
Module for interacting with a Java GATE process, running API commands on it and
exchanging data with it.
"""

import sys
import subprocess
import os
import socket
import platform as sysplatform
import glob
from py4j.java_gateway import JavaGateway, GatewayParameters
import logging
from gatenlp.docformats import  simplejson
import atexit

JARVERSION = "1.0"

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def classpath_sep(platform=None):
    """
    Return the classpath separator character for the current operating system / platform.

    :return: classpath separator character
    """
    if not platform:
        myplatform = sysplatform.system()
        if not myplatform:
            raise Exception("Could not determine operating system, please use platform parameter")
        platform = myplatform
    if platform.lower() == "windows":
        return ";"
    else:
        return ":"


def gate_classpath(gatehome, platform=None):
    """
    Return the GATE classpath components as a string, with the element seperator characters appropriate
    for the operating system.
    :param gatehome: where GATE is installed, either as a cloned git repo or a downloaded installation dir.
    :return: GATE classpath
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
            raise Exception("File not found {}, distribution may need compiling".format(cpfile))
        with open(cpfile, "rt", encoding="utf-8") as fp:
            cp = fp.read()
            return cp + cpsep + bindir
    else:
        # logger.info("DEBUG {} does not exist".format(cpfile))
        libdir = os.path.join(gatehome, "lib")
        bindir = os.path.join(gatehome, "bin")
        if not os.path.isdir(libdir):
            raise Exception("Could not determine class path from {}, no lib directory".format(gatehome))
        # jars = glob.glob(os.path.join(libdir,"*.jar"))
        # return cpsep.join(jars)
        return libdir + cpsep + bindir


class GateSlave:
    def __init__(self, port=25333, start=True, java="java", host="127.0.0.1", gatehome=None, platform=None):
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

        Example: ::

            gs = GateSlave()
            pipeline = gs.slave.loadPipelineFromFile("thePipeline.xgapp")
            doc = gs.slave.createDocument("Some document text")
            gs.slave.run4doc(pipeline,doc)
            pdoc = gs.gdoc2pdoc(doc)
            gs.slave.deleteResource(doc)
            # process the gatenlp Document pdoc ...

        :param port: port to use
        :param java: path to the java binary to run or the java command to use from the PATH (for start=True)
        :param host: host an existing Java GATE process is running on (only relevant for start=False)
        :param gatehome: where GATE is installed (only relevant if start=True). If None, expects
               environment variable GATE_HOME to be set.
        :param platform: system platform we run on, one of Windows, Linux (also for MacOs) or Java
        """
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
        if gatehome is None and start:
            gatehome = os.environ.get("GATE_HOME")
            if gatehome is None:
                raise Exception("Parameter gatehome is None and environment var GATE_HOME not set")
            self.gatehome = gatehome
        if start:
            # make sure we find the jar we need
            # logger.info("DEBUG: file location: {}".format(__file__))
            jarloc = os.path.join(os.path.dirname(__file__), "_jars", f"gatetools-gatenlpslave-{JARVERSION}.jar")
            if not os.path.exists(jarloc):
                raise Exception("Could not find jar, {} does not exist".format(jarloc))
            cmdandparms = []
            cmdandparms.append(java)
            cmdandparms.append("-cp")
            cpsep = classpath_sep(platform=platform)
            cmdandparms.append(jarloc + cpsep + gate_classpath(self.gatehome, platform=platform))
            cmdandparms.append("gate.tools.gatenlpslave.GatenlpSlave")
            cmdandparms.append(str(port))
            cmdandparms.append(host)
            subproc = subprocess.Popen(cmdandparms, stderr=subprocess.PIPE, bufsize=0, encoding="utf-8")
            self.gateprocess = subproc
            while True:
                line = subproc.stderr.readline().strip()
                if line == "PYTHON SLAVE SERVER OK":
                    break
                if line == "PYTHON SLAVE SERVER NOT OK":
                    raise Exception("Could not start server, giving up")
                print(line, file=sys.stderr)
            atexit.register(self.close)
        self.gateway = JavaGateway(gateway_parameters=GatewayParameters(port=port))
        self.jvm = self.gateway.jvm
        self.slave = self.gateway.entry_point

    def close(self):
        """
        Clean up: if the gate slave process was started by us, we will shut it down.
        :return:
        """
        if self.start and not self.closed:
            self.closed = True
            self.gateway.shutdown()
            for line in self.gateprocess.stderr:
                print(line, file=sys.stderr, end="")
            self.gateprocess.wait()

    def load_gdoc(self, path, mimetype=None):
        """
        Let GATE load a document from the given path and return a handle to it.

        :param path: path to the gate document to load.
        :param mimetype: a mimetype to use when loading.
        :return: a handle to the GATE document
        """
        if mimetype is None:
            mimetype = ""
        return self.slave.loadDocumentFromFile(path, mimetype)

    def save_gdoc(self, gdoc, path, mimetype=None):
        """
        Save GATE document to the given path.

        :param gdoc: GATE document handle
        :param path:  destination path
        :param mimetype: mimtetype, only the following types are allowed: ""/None: GATE XML,
               application/fastinfoset, and all mimetypes supported by the Format_Bdoc plugin.
        :return:
        """
        if mimetype is None:
            mimetype = ""
        self.slave.saveDocumentToFile(path, mimetype)

    def gdoc2pdoc(self, gdoc):
        """
        Convert the GATE document to a python document and return it.

        :param gdoc: the handle to a GATE document
        :return: a gatenlp Document instance
        """
        bjs = self.slave.getBdocJson(gdoc)
        return simplejson.loads(bjs)

    def pdoc2gdoc(self, pdoc):
        """
        Convert the Python gatenlp document to a GATE document and return a handle to it.

        :param pdoc: python gatenlp Document
        :return: handle to GATE document
        """
        json = simplejson.dumps(pdoc)
        return self.slave.getDocument4BdocJson(json)

    def load_pdoc(self, path, mimetype=None):
        """
        Load a document from the given path, using GATE and convert and return as gatenlp Python document.

        :param path: path to load document from
        :param mimetype: mime type to use
        :return: gatenlp document
        """
        gdoc = self.load_gdoc(path, mimetype)
        return self.gdoc2pdoc(gdoc)

    def del_gdoc(self, gdoc):
        """
        Delete/unload the GATE document from GATE.
        This is necessary to do for each GATE document that is not used anymore, otherwise the documents
        will accumulate in the Java process and eat up all memory. NOTE: just removing all references to the
        GATE document does not delete/unload the document!

        :param gdoc: the document to remove
        :return:
        """
        self.gate.Factory.deleteResource(gdoc)