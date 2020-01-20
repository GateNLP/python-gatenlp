#!/usr/bin/env python
# encoding: utf-8

"""Packaging script for the gatenlp library."""

import os
import subprocess
from setuptools import setup, find_packages
import re
from shutil import copyfile

JARFILE = "gatetools-gatenlpslave-1.0.jar"
JARFILE_PATH = os.path.join("java","target", JARFILE) # where it is after compiling
JARFILE_DIST = os.path.join("gatenlp", "_jars", JARFILE) # where it is for distribution
JAVAFILE_PATH = os.path.join("java", "src", "main", "java", "gate", "tools", "gatenlpslave", "GatenlpSlave.java")

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    readme = f.read()

def versionfromfile(*filepath):
    here = os.path.abspath(os.path.dirname(__file__))
    infile = os.path.join(here, *filepath)
    with open(infile) as fp:
        version_match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]",
                                  fp.read(), re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string in {}.".format(infile))

def make_java():
    if os.path.exists(JARFILE_DIST) and os.stat(JARFILE_DIST).st_mtime > os.stat(JAVAFILE_PATH).st_mtime:
        return
    os.chdir("java")
    retcode = subprocess.call("mvn package", shell=True)
    if retcode != 0:
        raise Exception("Could not build jar, exit code is {}".format(retcode))
    os.chdir("..")
    copyfile(JARFILE_PATH, JARFILE_DIST)

make_java()

setup(
    name="gatenlp",
    version=versionfromfile("gatenlp/__init__.py"),
    author="Johann Petrak",
    author_email="johann.petrak@gmail.com",
    description='GATE NLP implementation in Python.',
    long_description=readme,
    long_description_content_type='text/markdown',
    setup_requires=["pytest-runner"],
    install_requires=["sortedcontainers"],
    python_requires=">=3.5",
    tests_require=['pytest'],
    platforms='any',
    license="MIT",
    keywords="",
    url="https://github.com/GateNLP/python-gatenlp",
    packages=find_packages(),
    package_data = {"": [JARFILE]},  # wherever we store the jarfile, copy it into the installed package dir
    # data_files=[("share/gatenlp", [JARFILE_PATH])],
    test_suite='tests',
    classifiers=[
        # "Development Status :: 6 - Mature",
        # "Development Status :: 5 - Production/Stable",
        "Development Status :: 4 - Beta",
        # "Development Status :: 3 - Alpha",
        # "Development Status :: 2 - Pre-Alpha",
        # "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
      ],
    )

