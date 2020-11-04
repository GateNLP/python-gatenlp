# Python GateNLP 
## A Python package for NLP similar to the Java GATE NLP framework

This is a Python package for representing the basic elements of text processing
and NLP in a way that is very similar to the
[Java GATE NLP](https://gate.ac.uk/)
framework. 

Processed documents exported from Java GATE can be used and processed documents
exported from this package can be used by Java GATE. In addition this package:
* can be used as a Python library to perform NLP tasks
* run other NLP libraries like Stanford Stanza or Spacy and represent their processing results as 
  GateNLP annotations. 
* load GateNLP documents from various formats, including HTML, GATE XML, Bdoc Json, Bdoc Yaml, Bdoc MessagePack, Text and others and save
  to most of these formats
* Generate HTML that allows to view a document and selectively display annotations from certain annotation sets and with certain types and show
  their features 
* provides the code to allow using Python directly from GATE via the [GATE Python plugin](https://github.com/GateNLP/gateplugin-Python)
* allows to execute Java GATE API calls directly from the Python call, e.g.
  to run a Java GATE processing pipeline on a document and get back 
  the Processed document via the `GateSlave` class.

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

* [The Generated Python Documentation](pythondoc/gatenlp)
