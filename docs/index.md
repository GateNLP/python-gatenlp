# Python GateNLP 

## A Python NLP framework

Python GateNLP is an NLP and text processing framework implemented in Python. 

Python GateNLP represents documents and stand-off annotations very similar to 
the [Java GATE framework](https://gate.ac.uk/): [Annotations](annotations) describe arbitrary character ranges in the text and each annotation can have an arbitrary number of _features_.  [Documents](documents) can have arbitrary features and an arbitrary number of named [_annotation sets_](annotationsets), where each annotation set can have an arbitrary number of annotations which can overlap in any way. Python GateNLP documents can be exchanged with Java GATE by using the bdocjs/bdocym/bdocmp formats which are supported in Java GATE via the [Format Bdoc Plugin](https://gatenlp.github.io/gateplugin-Format_Bdoc/)

Other than many other Python NLP tools, GateNLP does not require a specific way of how text is split up into tokens, tokens can be represented by annotations in any way, and a document can have different ways of tokenization simultanously, if needed. Similarly, entities can be represented by annotations without restriction: they do not need to start or end at token boundaries and can overlap arbitrarily. 

GateNLP provides ways to process text and create annotations using [annotating pipelines](processing), which are sequences of one or more annotators. 
There are [gazetteer annotators](gazetteers) for matching text against gazetteer lists and annotators for a rule-like matching of complex annotation and text sequences (see [PAMPAC](pampac)).

There is also support for creating GateNLP annotations with other NLP packages like Spacy or Stanford Stanza.

The GateNLP document representation also optionally allows to track all changes
done to the document in a ["change log"](changelogs). 
Such changes can later be applied to other Python GateNLP or to  Java GATE documents.

This library also implements the functionality for the interaction with
a Java GATE process in two different ways:
* The [Java GATE Python plugin](http://gatenlp.github.io/gateplugin-Python/) can invoke a process running Python GateNLP to annotate GATE documents.
* Python code can remote-control a Jave GATE instance via the [GateNLP GateWorker](gateworker)

## Installation

Install GateNLP with all optional dependencies: 

`pip install -U gatenlp[all]`

For more details see [Installation](installation.md)

## Overview of the documentation:

NOTE: most of the documentation pages below can be viewed as HTML, as a Jupyter notebook (NB), and the Jupyter notebook can be downloaded 
for running on your own computer (NB-DL).

* [Installation](installation.md)
* [Getting Started](getting-started) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/getting-started.ipynb) / [NB-DL](getting-started.ipynb)
* The Document class and classes related to components of a document:
    * [Annotation](annotations) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/annotations.ipynb) / [NB-DL](annotations.ipynb)
    * [AnnotationSet](annotationsets) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/annotationsets.ipynb)) / [NB-DL](annotationsets.ipynb)
    * [Document](documents) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/documents.ipynb)) / [NB-DL](documents.ipynb)
* The Changelog class for recording changes to a document
    * [ChangeLogs](changelogs) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/changelogs.ipynb)) / [NB-DL](changelogs.ipynb)
* A [comparison with the Java GATE API](diffs2gate)
* The module for running python code from the GATE Python plugin
    * [GateInteraction](gateinteraction)
* The module for running Java GATE code from python
    * [GateWorker](gateworker) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/gateworker.ipynb)) / [NB-DL](gateworker.ipynb)
* Modules for interaction with other NLP packages and converting their documents
    * [`lib_spacy`](lib_spacy) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/lib_spacy.ipynb) / [NB-DL](lib_spacy.ipynb) for interacting with [Spacy](spacy.io/)
    * [`lib_stanza`](lib_stanza) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/lib_stanza.ipynb) / [NB-DL](lib_stanza.ipynb) for interacting with [Stanza](https://stanfordnlp.github.io/stanza/)
* Connecting to annotation services on the web:
    * [Client Annotators](client_annotators) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/client_annotators.ipynb) / [NB-DL](client_annotators.ipynb)
* Modules related to NLP processing:
    * [Corpora](corpora) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/corpora.ipynb) / [NB-DL](corpora.ipynb)
    * [Processing](processing) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/processing.ipynb) / [NB-DL](processing.ipynb)
    * [Tokenizers](tokenizers) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/tokenizers.ipynb) / [NB-DL](tokenizers.ipynb)
    * Matching strings and token sequences:
      * [Gazetteers](gazetteers) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/gazetteers.ipynb) / [NB-DL](gazetteers.ipynb)
      * [Regular Expressions Annotator](stringregex) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/stringregex.ipynb) / [NB-DL](stringregex.ipynb)
    * Complex Annotation Patterns for matching text and annotation sequences: 
      * [PAMPAC](pampac) / [NB](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/pampac.ipynb) / [NB-DL](pampac.ipynb)
      * [PAMPAC Reference](pampac-reference)

## Course Materials

* [Gate Course 2021 - Module 11 Slides](training/module11-python.slides.html)

## Change Log

* [Change Log](changes): show major changes in each release since 1.0.1

## Python API

[The Generated Python Documentation](pythondoc/gatenlp)
