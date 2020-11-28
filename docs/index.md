# Python GateNLP 
## A Python package for NLP similar to the Java GATE NLP framework

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
* Python code can remote-control a Jave GATE instance via the [GateNLP GateSlave](gateslave)

## Installation

Install GateNLP with all optional dependencies: 

`pip install -U gatenlpi[all]`

For more details see [Installation](installation.md)

## Overview of the documentation:

NOTE: most of the documentation pages below can be viewed as HTML, as a Jupyter notebook, and the Jupyter notebook can be downloaded 
for running on your own computer.

* [Installation](installation.md)
* [Getting Started](getting-started) / [Getting Started Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/getting-started.ipynb) / [Notebook Download](getting-started.ipynb)
* The Document class and classes related to components of a document:
    * [Annotation](annotations) / [Annotation Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/annotations.ipynb) / [Notebook Download](annotations.ipynb)
    * [AnnotationSet](annotationsets) / [AnnotationSet Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/annotationsets.ipynb)) / [Notebook Download](annotationsets.ipynb)
    * [Document](documents) / [Document Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/documents.ipynb)) / [Notebook Download](documents.ipynb)
* The Changelog class for recording changes to a document
    * [ChangeLogs](changelogs) / [ChangeLogs Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/changelogs.ipynb)) / [Notebook Download](changelogs.ipynb)
* A [comparison with the Java GATE API](diffs2gate)
* The module for running python code from the GATE Python plugin
    * [GateInteraction](gateinteraction)
* The module for running Java GATE code from python
    * [GateSlave](gateslave) / [GateSlave Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/gateslave.ipynb)) / [Notebook Download](gateslave.ipynb)
* Modules for interaction with other NLP packages and converting their documents
    * [`lib_spacy`](lib_spacy) / [`lib_spacy` Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/lib_spacy.ipynb) / [Notebook Download](lib_spacy.ipynb) for interacting with [Spacy](spacy.io/)
    * [`lib_stanza`](lib_stanza) / [`lib_stanza` Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/lib_stanza.ipynb) / [Notebook Download](lib_stanza.ipynb) for interacting with [Stanza](https://stanfordnlp.github.io/stanza/)
    * [`lib_stanfordnlp`](lib_stanfordnlp) for interacting with [StanfordNLP](https://stanfordnlp.github.io/stanfordnlp/)
* Connecting to annotation services on the web:
    * [Client Annotators](client_annotators) / [Client Annotators Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/client_annotators.ipynb) / [Notebook Download](client_annotators.ipynb)
* Modules related to NLP processing:
    * [Corpora](corpora) / [Corpora Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/corpora.ipynb) / [Notebook Download)(corpora.ipynb)
    * [Processing](processing) / [Processing Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/processing.ipynb) / [Notebook Download](processing.ipyn)
    * [Gazetteers](gazetteers) / [Gazetteers Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/gazetteers.ipynb) / [Notebook Download](gazetteers.ipyn)
    * Complex Annotation Patterns for matching text and annotation sequences: 
      * [PAMPAC](pampac) / [PAMPAC Notebook](https://nbviewer.jupyter.org/urls/gatenlp.github.io/python-gatenlp/pampac.ipynb) / [Notebook Download](pampac.ipynb)
      * [PAMPAC Reference](pampac-reference)

* [The Generated Python Documentation](pythondoc/gatenlp)
