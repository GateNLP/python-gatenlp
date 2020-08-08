# Installation


## Requirements

`gatenlp` components use a wide range of other packages and can interact with
a wide variety of NLP tools. Rather than pulling in all dependencies when
installing, `gatenlp` only requires a few essential packages and leaves it
to the users to install additional packages only if they want to use the
component that needs them. Here is an overview over the basic requirements
and groups of packages needed for specific components:

Basic requirements:
* in file `requirements.txt`
* `sortedcontainers>=2.0.0` - gets installed with `gatenlp`
* `requests`

Requirements for saving/loading/importing/exporting
* these are for anything beyond the bdoc-JSON standard format
* `msgpack`
* `pyyaml`
* `bs4`

Requirements for using the GATE slave:
* Java 8
* py4j
* GATE 8.6.1 or later

Requirements for using the bridges to other NLP tools:
* for StanfordNLP: `stanfordnlp`
* for Stanford Stanza: `stanza`
* for Spacy: `spacy`
* for NLTK: `nltk`

Requirements for development:
* `sphinx`
* Java SDK version 8
* Maven version 3.6
