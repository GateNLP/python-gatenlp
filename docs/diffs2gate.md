# Comparison with the GATE API

Generally, the priority in the `gatenlp` package is to make the API
pythonic, make use of Python features (e.g. keyword arguments) and use
names that are easy to remember and easy to understand when completion in
an IDE is used.

In the Jave GATE API, many functions are overloaded (e.g. AnnotationSet.get) and
return different things depending on the type of parameter(s). In the Python
API, the method name should make it clear what gets returned, unless it is
clear or easy to assume.

Also, most methods related to a kind of object are directly available through
the instance or class, e.g. in the Java GATE API, to create or load a document one has
to call a method of the Factory, to save a document one has to find the
correct Exporter class and call their method and so on. In Python `gatenlp`
all these actions are performed by methods on the class or instance.

## Documents:

There is no support or equivalent implementation for the
following GATE features and functionality in `gatenlp`:
* listeners
* editing, i.e. modifying the text of a document: once the document text is set, it is immutable. In order achieve a document with modified text, a new document must be created
* markup-aware/repositioning/preserveOriginalContent
* features work somewhat differently as it is not possible to replace the features object stored with a document or annotation, only modify it. 
* sourceUrlOffsets
* toXml: the GATE XML serialization format is not supported for saving. Instead the formats
  also implemented in the Java GATE [Format_Bdoc plugin](https://github.com/GateNLP/gateplugin-Format_Bdoc)
  are supported: Bdoc JSON and Bdoc MsgPack.
* DocumentContent: not necessary
* Additional document classes

There is no support or equivalent for the following GateNLP functions in GATE:
* `to_type`: to change offset type between java/python
* `set_changelog`: to record changes to a changelog
* `doc[span]`: where span is either an offset or offset range or an annotation
* a number of other methods of the AnnotationSet and Annotation classes

Here is a comparison of the most important API methods related to documents, showing first the GATE method, then the corresponding Python method (if any) and/or remarks:

* `getContent().size()`: `len(doc)`
* `getAnnotations()`: `annset()`
* `getAnnotations(name)`: `annset(name)`
* `getAnnotationSetNames()`: `annset_names()`
* `removeAnnotationSet(name)`: `remove_annset(name)`
* `|get/setContent()`:  -, not needed
* `get/setSourceUrl()`:  not needed internally, the end user can simply store this or any other  information about the document source in a document feature
* `add/removeDocumentListener(listener)`:  not needed as we do not have a GUI 
* `edit(...)`: not supported as `gatenlp` documents are immutable 
* `getEncoding()`: -, not needed: internally, all texts are Unicode, if a file with a different encoding should get loaded it can be done simply by passing an open file connection  that has been opened with the proper encoding. 
* `getMimeType():`  not needed not needed: the file format is specified when loading and not relevant once the Document has been created 
* `getNextAnnotationId()` not needed, ids are allocated per annotation set 
* getNextNodeId()`: not needed, the annotation set implementation does not use nodes |
* `getCollectRepositioningInfo():` not supported 
* `getMarkupAware()`: not supported
* `getPreserveOriginalContent()`: there is no support for "markup-awareness" 
* `toXml():`  `save()` -- saving to (or loading from) GATE XML format is not supported, saving/loading  using supported formats works via `doc.save(...)` and `Document.load(...)` 
* `get/setSourceUrlStart/EndOffset()`: not supported


## Features:

* So far, only Annotations and Documents can have features
* Features behave much like a Python dict
* Features are stored in a `Features` object
* The `Features` object for a Document or Annotation cannot be replaced
* Features *must* have string keys and should have values that are JSON-serializable
  (otherwise, the document cannot get saved in Bdoc JSPN format)

Setting a feature:
* GATE: `obj.getFeatures().put(name, value)`
* Python: `obj.features[name] = value`

Getting a feature:
* GATE: `obj.getFeatures().get(name)`
* Python: `obj.features.get(name [,defaulval])` or `obj.features[name]`

## Annotations:

The main differences and properties are:
* no listeners
* offsets are int not Long
* no nodes
* ! annotation ids are/have to be unique per set, not per document
* as for documents, the feature dictionary cannot be replaced as a whole, only be modified
* the offsets and type of an annotation are immutable
* ordering is based on increasing start offset, then increasing annotation id.

Here is a comparison of the most important API methods related to annotations,  showing first the GATE method, then the corresponding Python method (if any) and/or remarks:

* `coextensive(ann)`: `iscoextensive(annorsetorrange)` - many methods for annotations or annotation sets allow offset pairs, annotations or annotation sets to get used as an offset range
* `is[Partially]Compatible(ann)`: not implemented
* `overlaps(ann)`: `is overlapping(annorsetorrange)`
* `withinSpanOf(ann)`: `iswithin(annorsetorrange)`
* `getId()`: `id` this is an immutable property in Python
* `getType()`: `type`
* `getEndNode().getOffset()`: `end`
* `getStartNode().getOffset()`: `start`

Python also has `iscovering(annorsetorrange)` and `isinside(offset)` 

GATE methods `getEndNode()`, `getStartNode()` are not needed in Python. 

### AnnotationSet

