# Overview over the API


## Comparison with the GATE API

Generally, the priority in the `gatenlp` package is to make the API
pythonic, make use of Python features (e.g. keyword arguments) and use
names that are easy to remember and easy to understand when completion in
an IDE is used. E.g. avoid having method names like `get` where it is hard
to guess from just the parameter type how something gets retrieved.


#### Documents:


#### Features:

* So far, only Annotations and Documents can have features
* Manipulating features is done directly on the object that has features,
  not by retrieving a feature map instance first, e.g. `my_doc.set_feature("featurename", featurevalue)`
* Features must have string keys and should have values that are JSON-serializable
  (otherwise, the document cannot get saved in bdocjson format)

#### Annotation Sets:


#### Annotations:
