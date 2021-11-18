# Versions and changes

## 1.0.6 (upcoming)

* The minimum Python version has been changed from 3.6 to 3.7. This now allows the use of postponed evaluation of type annotations and the use of dataclasses. 
* add `Document.edit(edits, affected_strategy="keepadapt")` method: update document text and change offsets/indices for all annotations, if necessary.
* New annotator [StringRegexpAnnotator](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/processing/gazetteer/stringregex.html) which allows
  to annotate documents using Python regular expressions in a very simple and flexible way. See the 
  [StringRegexpAnnotator Documentation](https://gatenlp.github.io/python-gatenlp/stringregex).
* The [StringGazetteer](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/processing/gazetteer/stringgazetteer.html) has been implemented.
  See the [Gazetteers](https://gatenlp.github.io/python-gatenlp/gazetteers) documentation.
* The [TokenGazetteer](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/processing/gazetteer/tokengazetteer.html) parameter names got changed to match the corresponding `StringGazetteer` names
* ! the parameter name `out_set` in `gatenlp.processing.tokenizer` was changed to `outset_name` to be consistent with the name used elsewhere.
* ! the parameter name `out_annset` in `gatenlp.processing.client` was changed to `outset_name` to be consistent with the name used elsewhere.
* The `Document.clone()` method can be used to easily create an exact copy of a document, where none of the data is shared (deep copy)
* The [TextNormalizer](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/processing/normalizer.html) has been added. It can be used to normalize the unicode representation of the text in a document.
* loading a document from bdocjs format now does not require any keys in the JSON map and also ignores all 
  unknown keys. This allows to more easily import ad-hoc documents which e.g. only contain the text or text and 
  annotations (if not offset type is specified, python is assumed).
* The documentation has been updated and extended (especially for gazetteers and PAMPAC)

## 1.0.5.1 (2021-10-09)

* Bug fix: make `lib_spacy` support both versions 2.x and 3.x (1.0.5 used a method which is only available in 3.x)

## 1.0.5 (2021-10-08)

Changes that break backwards compatibility:

* `AnnotationSet.with_type()` previously returned a detached set with all annotations if no types were specified,
  this now returns a detached set with no annotations which is more logical. 
* API changes:
  * `pam.pampac.actions.AddAnn`: parameter `anntype` has been changed to `type`
  * The Feature() constructor kw arg `logger` has been changed to `_change_logger` and `deepcopy` has been changed to 
    `_deepcopy`
* Pampac: use the term "matches" instead of "data" for the named information stored for each named pattern that
  fits the document. A single one of these is often called "match info" and the index for a specific info is now called
  "matchidx" instead of "dataidx". See issue #89
* Parameter `spacetoken_type` for `AnnSpacy` and `spacy2gatenlp` has been changed to `space_token_type` to conform to 
  the parameter name used for `AnnStanza` and `stanza2gatenlp`.
* Stanford Stanza support now requires Stanza version 1.3.0 or higher
* Changes to `lib_spacy`: new parameter `containing_anns` to apply the spacy pipeline only to the part of the document  covered
  by each of the annotations in the annotation set or iterator. New parameters `component_cfg` to specify a component config
  for Spacy and `retrieve_spans` to retrieve additional span types to retrieve.
* Several bugfixes in Pampac.

Other changes and improvements:

* New method `AnnotationSet.create_from(anniterable)` to create a detached, immutable annotation set from an iterable of annotations
* New method `Document.anns(annspec)` creates a detached set of all annotations that match the specification
* New method `Document.yield_anns(annspec)` yields all annotations which match the specification
* Fixed bug in Token Gazetteer: issue #93
* Pampac: there is now a PampacAnnotator class to simplify using Pampac in a pipeline.
* Pampac: New parameter `containing_anns` for `Pampac.run`: if specified, runs the rules on each span of each of the containing annotations
* Pampac: a Result is now an Iterable of match infos.
* Pampac: the `.within(..)` `.contains(..)` etc. constraints now allow to use a separate annotation set, e.g.
  `.within("Person", annset=doc.annset("Other"))`. See issue #57
* Pampac: `RemoveAnn` action has been added
* Pampac: `UpdateAnnFeatures` has been improved
* Pampac: `AddAnn` action supports getter helpers in feature values
* `Span` objects are now immutable. Equality and hashing of `Span` objects are based on their start and end offsets.
* `Annotation` equality and hashing has been changed back to the Python default: variables compare only equal if they
  reference the same object and hashing is based on object identity. 
  For comparing annotations by content, the methods `ann.equal(other)` (compare content without annotation id) 
   and `ann.same(other)` (compare content including annotation id) have been implemented.
* Documents can be saved in "tweet-v1" format
* Fixed a problem with the HTML viewer: leading and multiple whitespace annotations now show correctly.



## 1.0.4 (2021-04-10)

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

