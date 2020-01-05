# Overview over the API


## Comparison with the GATE API

Generally, the priority in the `gatenlp` package is to make the API
pythonic, make use of Python features (e.g. keyword arguments) and use
names that are easy to remember and easy to understand when completion in
an IDE is used. E.g. avoid having method names like `get` where it is hard
to guess from just the parameter type how something gets retrieved.


#### Documents:

There is no support or equivalent implementation for the
following GATE features and functionality in `gatenlp`:
* listeners
* editing: once the document text is set, it is immutable. In order achieve a document with modified text, a new document must be created
* markup-aware/repositioning/preserveOriginalContent
* sourceUrlOffsets
* toXml: the GATE XML serialization format is not supported, use bdocjson instead
* DocumentContent: not necessary since only text is supported

The following should maybe get supported?
* get/setSourceUrl(URL)
* hide annotation set implementation as a default dict and provide API for removing a set? NOTE: if a user currently just removes a set from the dict, that event does not get added to the changelog!


There is no support or equivalent for the following `gatenlp` functions in GATE:
* `to_type`: to change offset type between java/python
* `set_changelog`: to record changes to a changelog
* `[span]`: where span is either an offset or offset range or an annotation

|GATE|gatenlp|Comment
|---|---|---|
|getAnnotations()|get_annotations()|  |


<table>
<tr><th>GATE</th><th>gatenlp</th><th>Comment</th></tr>
<tr><td>getAnnotations()</td><td>get_annotations()</td><td></td></tr>
<tr><td>getAnnotations(name)</td><td>get_annotations(name)</td><td></td></tr>
<tr><td>getAnnotations(name)</td><td>get_annotations(name)</td><td></td></tr>
<tr><td>removeAnnotationSet(name)</td><td>MISSING</td><td>probably should get added</td></tr>

</table>



#### Features:

* So far, only Annotations and Documents can have features
* Manipulating features is done directly on the object that has features,
  not by retrieving a feature map instance first, e.g. `my_doc.set_feature("featurename", featurevalue)`
* Features must have string keys and should have values that are JSON-serializable
  (otherwise, the document cannot get saved in bdocjson format)

#### Annotation Sets:


#### Annotations:
