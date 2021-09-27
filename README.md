# Python library gatenlp

[![PyPi version](https://img.shields.io/pypi/v/gatenlp.svg)](https://pypi.python.org/pypi/gatenlp/)
[![Python compatibility](https://img.shields.io/pypi/pyversions/gatenlp.svg)](https://pypi.python.org/pypi/gatenlp/)
[![Downloads](https://static.pepy.tech/personalized-badge/gatenlp?period=week&units=none&left_color=blue&right_color=yellow&left_text=Downloads/week)](https://pepy.tech/project/gatenlp)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gatenlp)](https://pypistats.org/packages/gatenlp)
[![License](https://img.shields.io/github/license/GateNLP/python-gatenlp.svg)](LICENSE)
[![GitHub Build Status](https://github.com/GateNLP/python-gatenlp/actions/workflows/python-package.yml/badge.svg?branch=main)](https://github.com/GateNLP/python-gatenlp/actions/workflows/python-package.yml)
[![CodeCov](https://img.shields.io/codecov/c/gh/GateNlp/python-gatenlp.svg)](https://codecov.io/gh/GateNLP/python-gatenlp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Join the chat at https://gitter.im/GateNLP/python-gatenlp](https://badges.gitter.im/GateNLP/python-gatenlp.svg)](https://gitter.im/GateNLP/python-gatenlp?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Documentation Status](https://readthedocs.org/projects/gatenlp/badge/?version=latest)](https://gatenlp.readthedocs.io/en/latest/?badge=latest)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/ccc55f10e7f5479e9a882ec3aee3222a)](https://www.codacy.com/gh/GateNLP/python-gatenlp/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=GateNLP/python-gatenlp)
[![Updates](https://pyup.io/repos/github/GateNLP/python-gatenlp/shield.svg)](https://pyup.io/repos/github/GateNLP/python-gatenlp/)
[![Python 3](https://pyup.io/repos/github/GateNLP/python-gatenlp/python-3-shield.svg)](https://pyup.io/repos/github/GateNLP/python-gatenlp/)


![Python GateNLP](https://github.com/GateNLP/python-gatenlp/blob/main/docs/logo/gateNLP-423x145.png)

Python package for:
* Representing documents, annotations, annotation and document features etc. 
* Processing documents with powerful NLP libraries like Stanza, Spacy, NLTK and represent results as gatenlp annotations and features
* Visualize annotations and features using interactive HTML and allow those visualizations to be included in Jupyter or Colab notebooks
* Using a powerful pattern matching library (PAMPAC) to match complex patterns based on text, annotations and features and create new annotations
* Interact with and use Java GATE from Python
* Allow to use Python processing from Java GATE via the GATE Python plugin
* Provide abstractions for building complex processing pipelines

## Documentation and feedback

* Documentation:
  * [GitHub](https://gatenlp.github.io/python-gatenlp/) 
  * [ReadTheDocs](https://gatenlp.readthedocs.io/en/latest/)
* PythonDoc:
  * [GitHub](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/)
  * [ReadTheDocs](https://gatenlp.readthedocs.io/en/latest/pythondoc/gatenlp/)

If you find bugs, want to requrest a feature or change, please use the [issue tracker](https://github.com/GateNLP/python-gatenlp/issues)

For more general discussions about the package and communication within current and future users, please use the [Dicussions](https://github.com/GateNLP/python-gatenlp/discussions)


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

## Versions and Roadmap

* Versions 0.x are unpublished
* Versions 1.0.x are public releases with feedback that may change APIs and change main parts of the software
* Versions 1.x are public stable releases

## Default branch renamed to "main"

If you have a cloned copy, you need to rename it in your local copy as well:
```
git branch -m master main
git fetch origin
git branch -u origin/main main
```



---

**NOTE: The previous Pypi project "gatenlp" has moved to [gatenlphiltlab](https://github.com/nickwbarber/gatenlphiltlab)**

