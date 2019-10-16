# Python library gatenlp

[![PyPi version](https://img.shields.io/pypi/v/gatenlp.svg)](https://pypi.python.org/pypi/gatenlp/)
[![Python compatibility](https://img.shields.io/pypi/pyversions/gatenlp.svg)](https://pypi.python.org/pypi/gatenlp/)


Library for manipulating [GateNLP](https://gate.ac.uk/) documents and
for interacting with GATE Java and the GATE python plugin.

**NOTE: This is in the planning/development stage for now**

**NOTE: The original Pypi project "gatenlp" has moved to [gatenlphiltlab](https://github.com/nickwbarber/gatenlphiltlab) **

## Overview

This library can load GATE documents from their BdocJS (JSON) representation
or create GATE documents from scratch. This creates an object of type
`gatenlp.Document` which offers an API for adding, retrieving and changing
stand-off annotations and document features
in much the same way as this is done in Java GATE.

This document representation also optionally allows to track all changes
done to the document in a "change log" (a `gatenlp.ChangeLog` instance).
Such changes can later be applied to Java GATE documents.

This library also implements the functionality for the interaction with
a Java GATE process in two different ways:
* The Java GATE Python plugin can invoke a python process to annotate GATE documents
  with python code
* the python code can remote-control a Jave GATE instance (NOT YET IMPLEMENTED!)

## More information and documentation

* [Documentation](https://gatenlp.github.io/python-gatenlp/) with
  * [Usage Examples](https://gatenlp.github.io/python-gatenlp/UsageExamples)
  * [Tutorial](https://gatenlp.github.io/python-gatenlp/Tutorial) TBD!
  * [PythonDoc](https://gatenlp.github.io/python-gatenlp/pythondoc/)
