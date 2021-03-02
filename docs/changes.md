# Versions and changes

## (upcoming)

* Issue #66: make it possible to show annotations over new-lines in the html ann viewer
* Issue #65: provide ParagraphTokenizer and SplitPatternTokenizer to easily annotate paragraphs
  and other spans separated by some split pattern

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

