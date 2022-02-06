#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import re
from shutil import copyfile
import subprocess

JARFILE = "gatetools-gatenlpworker-1.0.jar"
JARFILE_PATH = os.path.join("java", "target", JARFILE)  # where it is after compiling
JARFILE_DIST = os.path.join(
    "gatenlp", "_jars", JARFILE
)  # where to put the jarfile prior before running setup
JARFILE_DEST = os.path.join(
    "_jars", JARFILE
)  # where it should be relative to the gatenlp package
JAVAFILE_PATH = os.path.join(
    "java", "src", "main", "java", "gate", "tools", "gatenlpworker", "GatenlpWorker.java"
)


def make_java():
    if (
        os.path.exists(JARFILE_DIST)
        and os.stat(JARFILE_DIST).st_mtime > os.stat(JAVAFILE_PATH).st_mtime
    ):
        return
    os.chdir("java")
    retcode = subprocess.call("mvn package", shell=True)
    if retcode != 0:
        raise Exception("Could not build jar, exit code is {}".format(retcode))
    os.chdir("..")
    copyfile(JARFILE_PATH, JARFILE_DIST)


make_java()
