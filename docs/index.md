# gatenlp - A package for NLP similar to the Java Gate NLP framework

This is a package for representing the basic elements of text processing
and NLP in a way that is very similar to the
[Java GATE NLP](https://gate.ac.uk/)
framework.

Processed documents exported from Java GATE can be used and processed documents
exported from this package can be used by Java GATE. In addition this package:
* provides the code to allow using Python directly from GATE via the [GATE Python plugin](https://github.com/GateNLP/gateplugin-Python)
* allows to execute Java GATE API calls directly from the Python call, e.g.
  to run a Java GATE processing pipeline on a document and get back 
  the Processed document via the `GateSlave` class.

NOTE: the current version provides mainly the means to represent and convert
documents, annotations etc. Actual NLP processing will be added as
development continues.

## Installation

`pip install -U gatenlp`

## Requirements

Requirements:
* Python 3.5 or later
* sortedcontainers
* msgpack

Additional requirements only needed if certain functions are used:
* py4j

Additional requirements for supported interaction with other NLP 
packages:
* stanfordnlp
* stanza
* spacy

## Overview of the documentation:

* The Document class and classes related to components of a document:
  * [Document](documents)
  * [AnnotationSet](annotationsets)
  * [Annotation](annotations)
* The Changelog class for recording changes to a document
  * [ChangeLog](changelogs)
* [Usage examples](usage-examples)  
* A [comparison with the Java GATE API](diffs2gate)
* The module for running python code from the GATE Python plugin
  * [GateInteraction](gateinteraction)
* The module for running Java GATE code from python
  * [GateSlave](gateslave)
* Modules for interaction with other NLP packages and converting their documents
  * [`lib_spacy`](lib_spacy) for interacting with [Spacy](spacy.io/)
  * [`lib_stanza`](lib_stanza) for interacting with [Stanza](https://stanfordnlp.github.io/stanza/)
  * [`lib_stanfordnlp`](lib_stanfordnlp) for interacting with [StanfordNLP](https://stanfordnlp.github.io/stanfordnlp/)
* Modules for basic NLP processing (in development):
  * [Gazetteers](gazetteers) NOT YET
  * [Annotation Rules/Patterns: ARUPAC](arupac) NOT YET
  * [Machine Learning](ml) NOT YET
* [Comparison to other Python NLP packages](comparison)

* [The Generated Python Documentation](pythondoc)
