# Python library gatenlp

[![PyPi version](https://img.shields.io/pypi/v/gatenlp.svg)](https://pypi.python.org/pypi/gatenlp/)
[![Python compatibility](https://img.shields.io/pypi/pyversions/gatenlp.svg)](https://pypi.python.org/pypi/gatenlp/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gatenlp)](https://pypistats.org/packages/gatenlp)
[![License](https://img.shields.io/github/license/GateNLP/python-gatenlp.svg)](LICENSE)
[![Travis](https://travis-ci.com/GateNLP/python-gatenlp.svg?branch=master)](https://travis-ci.com/github/GateNLP/python-gatenlp)
[![CodeCov](https://img.shields.io/codecov/c/gh/GateNlp/python-gatenlp.svg)](https://codecov.io/gh/GateNLP/python-gatenlp)

This is a package for representing the basic elements of text processing
and NLP in a way that is very similar to the
[Java GATE NLP](https://gate.ac.uk/)
framework, 
for manipulating GateNLP documents and
for interacting with GATE Java and the GATE python plugin.

**NOTE: The previous Pypi project "gatenlp" has moved to [gatenlphiltlab](https://github.com/nickwbarber/gatenlphiltlab)**

## Overview

This package is a Python implementation of text processing and NLP similar to
[Java GATE NLP](https://gate.ac.uk/).
Currently it is possible to load GATE documents from their BdocJS (JSON) representation
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
* the python code can remote-control a Jave GATE instance

## More information and documentation

* [Documentation](https://gatenlp.github.io/python-gatenlp/) with
  * [Usage Examples](https://gatenlp.github.io/python-gatenlp/usage-examples)
  * [Tutorial](https://gatenlp.github.io/python-gatenlp/tutorial) 
  * [PythonDoc](https://gatenlp.github.io/python-gatenlp/pythondoc/)
