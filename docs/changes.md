# Versions and changes

## (upcoming)

* The GateWorkerAnnotator parameters have been changed: instead of parameters gatehom and port,
  the parameter gateworker now needs to receive a GateWorker instance. 
  Also the `update_document` parameter has been added and now allows both updating and replacing
  the Python document from the Java GATE document
* Issue #66: make it possible to show annotations over new-lines in the html ann viewer
* Issue #65: provide ParagraphTokenizer and SplitPatternTokenizer to easily annotate paragraphs
  and other spans separated by some split pattern
* Issue #73: pickle document with offset index created
* Issue #68: rename the main development branch from "master" to "main"
* Issue #74: fix a bug in PAMPAC related to matching an annotation after some text
* Various improvements, additions and bug fixes in Pampac
* Issue #75: GateWorker now shows any Java exception when starting the Java process fails
* Issue #76: GateWorker has a new method `loadPipelineFromUri(uri)`
* Issue #77: GateWorkerAnnotator now automatically loads a pipeline from a URL if the string
  passed to the `pipeline` parameter looks like a URL or if it is the result of urllib.parse.urlparse.
  It is always treated like a file if it is a pathlib.Path
* added the `Actions` action for Pampac to recursively wrap several actions into one
* allow each Rule to have any number of actions, change signature to `Rule(patter, *actions, priority=0)`
* The Pampac AddAnn action does not require a value for the name parameter any more, if not specified, the 
  full span of the match is used.
* New method `add_anns(anniterable)` to add an iterable of annotations to a set
* The document viewer now also works in Google Colab
* The GateWorker can now be used as context manager: `with GateWorker() as gw:`


## 1.0.3.1 (2021-03-01)

* add training course slides
* fix issue #63: could not import html document from a local file
 
## 1.0.3 (2021-02-22) 

* Fix issues with logging and error handling in executor module
* Improve/add/change document sources/destination JsonLinesFile
* add `Span.embed` method
* Implement multi-word tokens (MWTs) for the Stanza annotator
* Add support for space tokens for the Stanza annotator
* Support showing annotations over trailing spaces in the html ann viewer
* Add the `Document.attach(annset)` method (mostly for internal use only!)
* Add the ConllUFileSource to import CoNLL-U corpora
* Fix a problem in the html ann viewer where unnecessary spans were created
* Add option to the `Document.show()` method to style the document text div


## 1.0.2 (2021-02-09)

* Fix issue #56: Rename GateSlave to GateWorker

## 1.0.1 (2021-02-07)

* Initial release
~                                                                                                                                                     

