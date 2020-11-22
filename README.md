# Python library gatenlp

[![PyPi version](https://img.shields.io/pypi/v/gatenlp.svg)](https://pypi.python.org/pypi/gatenlp/)
[![Python compatibility](https://img.shields.io/pypi/pyversions/gatenlp.svg)](https://pypi.python.org/pypi/gatenlp/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gatenlp)](https://pypistats.org/packages/gatenlp)
[![License](https://img.shields.io/github/license/GateNLP/python-gatenlp.svg)](LICENSE)
[![Travis](https://travis-ci.com/GateNLP/python-gatenlp.svg?branch=master)](https://travis-ci.com/github/GateNLP/python-gatenlp)
[![CodeCov](https://img.shields.io/codecov/c/gh/GateNlp/python-gatenlp.svg)](https://codecov.io/gh/GateNLP/python-gatenlp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is a package for representing the basic elements of text processing
and NLP in a way that is very similar to the
[Java GATE NLP](https://gate.ac.uk/)
framework, 
for manipulating GateNLP documents and
for interacting with GATE Java and the GATE python plugin.

## Overview

Python GateNLP is an NLP and text processing framework implemented in Python. 

Python GateNLP represents documents and stand-off annotations very similar to 
the [Java GATE framework](https://gate.ac.uk/): Annotations describe arbitrary character ranges in the text and each annotation can have an arbitrary number of _features_.  Documents can have arbitrary features and an arbitrary number of named _annotation sets_, where each annotation set can have an arbitrary number of annotations which can overlap in any way. Python GateNLP documents can be exchanged with Java GATE by using the bdocjs/bdocym/bdocmp formats which are supported in Java GATE via the [Format Bdoc Plugin](https://gatenlp.github.io/gateplugin-Format_Bdoc/)

Other than many other Python NLP tools, GateNLP does not require a specific way of how text is split up into tokens, tokens can be represented by annotations in any way, and a document can have different ways of tokenization simoultanously, if needed. Similarly, entities can be represented by annotations without restriction: they do not need to start or end at token boundaries and can overlap arbitrarily. 

GateNLP provides ways to process text and create annotations using annotating pipelines, which are sequences of one or more annotators. 
There are annotators for matching text against gazetteer lists and annotators for complex matching of annotation and text sequences (see [PAMPAC](pampac)).

There is also support for creating GateNLP annotations with other NLP packages like Spacy or Stanford Stanza.

The GateNLP document representation also optionally allows to track all changes
done to the document in a "change log" (a `gatenlp.ChangeLog` instance).
Such changes can later be applied to other Python GateNLP or to  Java GATE documents.

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

---

**NOTE: The previous Pypi project "gatenlp" has moved to [gatenlphiltlab](https://github.com/nickwbarber/gatenlphiltlab)**

