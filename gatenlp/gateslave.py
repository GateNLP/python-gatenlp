#!/usr/bin/env python
"""
Module for interacting with a Java GATE process, running API commands on it and
exchanging data with it.
The main method allows to run some of this from the command line using command line arguments.
"""

import sys
import subprocess
import os
import platform as sysplatform
import glob
from py4j.java_gateway import JavaGateway, GatewayParameters
import logging

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
    cpfile = os.path.join(gatehome, "gate.classpath")
    logger.info("DEBUG checking for {}".format(cpfile))
    if os.path.exists(cpfile):
        if not os.path.exists(cpfile):
            raise Exception("File not found {}, distribution may need compiling".format(cpfile))
        with open(cpfile, "rt", encoding="utf-8") as fp:
            cp = fp.read()
            return cp
    else:
        logger.info("DEBUG {} does not exist".format(cpfile))
        cpsep = classpath_sep(platform)
        libdir = os.path.join(gatehome, "lib")
        if not os.path.isdir(libdir):
            raise Exception("Could not determine class path from {}, no lib directory".format(gatehome))
        jars = glob.glob(os.path.join(libdir,"*.jar"))
        return cpsep.join(jars)


class GateSlave:
    # TODO: handle proper shutdown of the GATE process (only if we started, otherwise only if started=True)
    # TODO: handle proper waiting for slave being ready!
    # TODO: think of API
    # TODO: make sure we have classloaders properly set up for the slave class (the LR)
    def __init__(self, port=25333, start=True, java="java", host="127.0.0.1", gatehome=None, platform=None):
        """
        Create an instance of the GateSlave and either start our own Java GATE process for it to use
        (start=True) or connect to an existing one (start=False).

        After initializing, the gateway attribute can be directly used or one of the convenience methods
        of this object be used for more complex tasks.

        :param port: port to use
        :param java: path to the java binary to run or the java command to use from the PATH (for start=True)
        :param host: host an existing Java GATE process is running on (only relevant for start=False)
        :param gatehome: where GATE is installed (only relevant if start=True). If None, expects\
        environment variable GATE_HOME to be set.
        :param platform: system platform we run on, one of Windows, Linux (also for MacOs) or Java
        """
        self.gatehome = gatehome
        self.port = port
        self.host = host
        self.platform = platform
        self.gateprocess = None
        self.gateway = None
        if gatehome is None and start:
            gatehome = os.environ.get("GATE_HOME")
            if gatehome is None:
                raise Exception("Parameter gatehome is None and environment var GATE_HOME not set")
            self.gatehome = gatehome
        if start:
            # make sure we find the jar we need
            logger.info("DEBUG: file location: {}".format(__file__))
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
            subproc = subprocess.Popen(cmdandparms)
            self.gateprocess = subproc
        self.gateway = JavaGateway(gateway_parameters=GatewayParameters(port=port))

    def close(self):
        """
        Terminate the processes.
        :return:
        """
        self.gateway.close()

    def load_gdoc(self):
        """
        NOT IMPLEMENTED YET
        :return:
        """
        # TODO: load GATE document and return handle to GATE document
        pass

    def gdoc2pdoc(self, gdoc):
        """
        NOT IMPLEMENTED YET
        :param gdoc:
        :return:
        """
        # TODO: convert a gate document to a python document
        pass

    def load_pdoc(self):
        """
        NOT IMPLEMENTED YET
        :return:
        """
        # TODO: directly load a python document by loading the gate document on the java side,
        # convert it to bdoc on the java side, convert to json, fetch json and convert to pdoc on python
        pass
