# Supported formats for documents and corpora

NOTE: this document is still work in progress!!

This document gives an overview over which formats GateNLP can use to

* load individual Documents from
* save individual Documents to
* read a sequence of documents (DocumentSource)
* write a sequence of documents (DocumentDestination)

NOTE: the standard format for loading/saving documents is a JSON representation of the document content
(optionally gzip compressed) and called `bdocjs`. A detailed description of this format can be found 
in [Format bdocjs](format-bdocjs.md)


## Loading individual Documents

To load a document the method `Document.load(source, ...)` can be used (see [PythonDoc](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/document.html#gatenlp.document.Document.load)). The `source` parameter is used to specify where the document should get loaded from:

* if `source` is a string, it is interpreted as the path to a file to load, except if the string starts with "http://" or "https://" in which case 
  the string is interpreted as the URL to load the document from. 
* if `source` is a `pathlib.Path` object, the corresponding file is loaded, even if the path starts with "http://" or "https://"
* if `source` is the result of `urllib.parse.urlparse`, that URL is always used for loading
* NOTE: not all formats support loading from an URL, in those cases a string is always interpreted as the file path

### Supported formats for loading

If the `fmt` parameter for the `load` method is None (the default), then an attempt is made to infer the format from the file extension of the path or URL 
(the characters after the last dot in the string that follows any path separator). 

If the extension is missing or does not properly indicate the format, the `fmt` parameter should specify a known mime-type like format specification or 
a known format identifier. The following list shows the supported formats and which format identifiers and extensions are associated with them:

* Format: bdocjs
  * extensions: `bdocjs`
  * identifier: `json`, `bdocjs`, `text/bdocjs`
  * A JSON-based format, can be exchanged with Java GATE using the `Format_bdoc` plugin. This format fully supports all document content and 
    all feature values which are JSON serializable, does not support shared objects or reference cycles in feature values. 
  * this is the recommended standard format
* Format: bdocjsgz
  * extensions: `bdocjs.gz`, `bdoc.gz`
  * identifier: `bdocjsgz`, `jsongz`, `text/bdocjs+gzip`
  * Same as bdocjs, but with gzip-compression
* Format: yaml
* Format: yamlgz
* Format: msgpack
* Format: text
* Format: html
* Format: html-rendered
* Format: gatexml
* Format: tweet-v1
* Format: pickle

### Supported formats for saving


* Format: bdocjs
* Format: bdocjsgz
* Format: yaml
* Format: yamlgz
* Format: msgpack
* Format: tweet-v1
* Format: html-ann-viewer


## Saving individual Documents


## Reading a sequence of documents


## Writing a sequence of documents
