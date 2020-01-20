# Overview over the API


## Comparison with the GATE API

Generally, the priority in the `gatenlp` package is to make the API
pythonic, make use of Python features (e.g. keyword arguments) and use
names that are easy to remember and easy to understand when completion in
an IDE is used. E.g. avoid having method names like `get` where it is hard
to guess from just the parameter type how something gets retrieved.


### Documents:

There is no support or equivalent implementation for the
following GATE features and functionality in `gatenlp`:
* listeners
* editing: once the document text is set, it is immutable. In order achieve a document with modified text, a new document must be created
* markup-aware/repositioning/preserveOriginalContent
* sourceUrlOffsets
* toXml: the GATE XML serialization format is not supported, use bdocjson instead
* DocumentContent: not necessary since only text is supported


There is no support or equivalent for the following `gatenlp` functions in GATE:
* `to_type`: to change offset type between java/python
* `set_changelog`: to record changes to a changelog
* `[span]`: where span is either an offset or offset range or an annotation

|GATE|gatenlp|Comment
|---|---|---|
|getAnnotations()|get_annotations()| - |
|getAnnotations(name)|get_annotations(name)| - |
|getAnnotationSetNames() | get_annotation_set_names() | - |
|removeAnnotationSet(name)|remove_annotation_set(name)| - |
|get/setContent() | - | not necessary, text can be accessed directly|
|get/setSourceUrl() | ???? | ?????? |
|add/removeDocumentListener(listener)| - | no listeners in gatenlp |
|edit(...)| - | gatenlp are immutable |
|getEncoding()| - | not needed (1) |
|getMimeType() | - | not needed (1) |
|getNextAnnotationId()|-| not needed, ids are allocated per set|
|getNextNodeId()|-| implementation does not use Nodes |
|getCollectRepositioningInfo()| - | not needed(1) |
|getMarkupAware() | - | not needed(1) |
|getPreserveOriginalContent() | - | not needed(1) |
|toXml| - | not implemented, use simplejson |
|get/setSourceUrlStart/EndOffset| - | not needed |


Remarks:
* (1): these Java GATE methods are only relevant during the original loading/parsing phase



### Features:

* So far, only Annotations and Documents can have features
* Manipulating features is done directly on the object that has features,
  not by retrieving a feature map instance first, e.g. `my_doc.set_feature("featurename", featurevalue)`
* Features must have string keys and should have values that are JSON-serializable
  (otherwise, the document cannot get saved in bdocjson format)


### Annotations:

The main differences and properties are:
* no listeners
* offsets are int not Long
* no nodes
* ! annotation ids are/have to be unique per set, not per document
* as for documents, features are set directly on the annotation, not by retrieving a feature map first
* the offsets and type of an annotation are immutable
* ordering is based on increasing start offset, then increasing end offset, then increasing type name, then increasing annotation id. Features are not considered for ordering.
* Equality is based on identity: annotations are only equal if the have the same id and come from the same set (which identifies them uniquely). The hash code corresponds to this definition. This allows to store several annotations over the same span, with the same type and features in a set.


|GATE|gatenlp|Comment
|---|---|---|
|coextensive()|
|getType()|type|-|

### AnnotationSet

|GATE|gatenlp|Comment
|---|---|---|
|add()|get_annotations()| one method instead of many overloaded ones |
|add(Annotation) | add_ann | - |
|inDocumentOrder()| (default iterator) | see 1) |

1) All the methods that return selections of annotations in the set, return
an immutable annotation set which can be directly iterated over. The
methods `iter(...)` and `reverse_iter` can be used to generate annotations in
document and apply some filters to them as well. 
