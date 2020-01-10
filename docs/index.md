# gatenlp - A package for NLP similar to the Java Gate NLP framework

This is a package for representing the basic elements of text processing
and NLP in a way that is very similar to the
[Java GATE NLP](https://gate.ac.uk/)
framework.

Processed documents exported from Java GATE can be used and processed documents
exported from this package can be used by Java GATE. In addition this package:
* provides the code to allow using Python directly from GATE via the [GATE Python plugin](https://github.com/GateNLP/gateplugin-Python)
* allows to execute Java GATE API calls directly from the Python call, e.g.
  to run a Java GATE processing pipeline on a document and get back the Processed
  document.

NOTE: the current version provides mainly the means to represent and convert
documents, annotations etc. Actual NLP processing will be added as
development continues.

## Installation

`pip install -U gatenlp`

## Requirements

Requirements:
* Python 3.4 or later
* sortedcontainers
* For Python 3.4 the module "typing" is required

## Overview of the documentation:

* [Comparison to other Python NLP packages](comparison)
* [Usage Examples](usage-examples)
* [API Overview and comparison with Java GATE](api)
* [The Generated Python Documentation](pythondoc)
