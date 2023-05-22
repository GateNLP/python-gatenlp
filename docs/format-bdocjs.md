# Format bdocjs/bdocjsgz

The "Basic Document" or "Bdoc" representation is a simple way to represent GATE documents, features, annotation sets and annotations
through basic datatypes like strings, integers, maps and arrays so that the same representation can be easily used 
from several programming languages. The representation is limited to the following data types: string, integer, float, boolean, array/list, map (basically what is supported by basic JSON). 

The `bdocjs` file format is a JSON serialization of that bdoc representation of a document as a map/dictionary usually stored as a file with the ".bdocjs" extension. The `bdocjsgz` file format is simply a gzip-compressed `bdocjs` file usually stored as a file with the `.bdocjs.gz` extension.


## API

* loading uncompressed: `doc = Document.load("SOMEFILE.bdocjs")` or `doc = Document.load("SOMEFILE.SOMEEXT", fmt="bdocjs")` if the extension is not `bdocjs`. 
* loading compressed: same as loading uncompressed but use extension "bdocjs.gz" or `fmt="bdocjsgz"` instead
* saving uncompressed: `doc.save("SOMEFILE.bdocjs")` or `doc.save("SOMEFILE.SOMEEXT", fmt="bdocjs")`
* saving compressed: same as saving uncompressed but use extension "bdocjs.gz" or `fmt="bdocjsgz"` instead
* converting a document to a JSON string of its `bdoc` representation: `doc.save_mem()`
* converting a document to its `bdoc` dictionary representation: `doc.to_dict()`
* creating a document from its `bdoc` dictionary representation: `doc = Document.from_dict(thebdocdict)`



## The abstract BdocDocument representation 

A document is map with the following keys. All keys are optional!

* `name` (String): the document name, if missing, the empty string is used as the document name.
* `text` (String): the document text , if missing a document without text is created (NOTE: documents without text do have limited support in gatenlp!)
* `offset_type` (String, either "p" or "j"): how offsets represent the individual code points in the text: either as the number of code point as in in Python (p) or as the number of UTF-16 code units as in Java (j). If missing, "p" is assumed when loading into gatenlp. 
* `annotation_sets` (Map): annotation set names mapped to a map representing an annotation set (see below). If missing, the list of annotation sets is empty.
* `features` (Map, see below): the document features, if missing an empty feature map is created. 

The document text must be able to represent any Unicode text and different serialization methods may use different ways of how to encode the text. 

Features are represented as a map:

* map a feature name to a feature value
* a feature name must be a non-null String
* a feature value must be one of the following basic data types: string, integer, float, boolean, array/list, map (essentially what is supported by basic JSON)
* shared references to the same data object (e.g. two features referencing the same list) are possible but may not be preserved by a specific serialization format. 
* recursive data structures (e.g. an element of an array being the array itself) are not allowed 

An Annotation set is represented as a map with the following keys:

* `annotations` (list): a list of maps representing the annotation (see below)
* `next_annid` (int): the next annotation id that can be assigned in this set
* `name` (str): (optional), if present the name of the annotation set which MUST match
  the key under which the set is present within the `annotation_sets` map, if missing the  key is used.

Annotations are represented as a map with the following keys:

* `start` (Integer):  the start offset of the annotation
* `end` (Integer): the end offset of the annotation
* `type` (String): the annotation type name of the annotation, should not be an empty string or a string containing only white space
* `id` (Integer): the "annotation id" a unique number assigned to each annotation in a set
* `features` (Map): features as described above for the document features.

## Examples

Here is a simple examle document serialized as JSON (bdocjs):

```
{
   "offset_type" : "p",
   "name" : "",
   "features" : {
      "feat1" : "value1"
   },
   "annotation_sets" : {
      "" : {
         "annotations" : [
            {
               "end" : 2,
               "id" : 0,
               "features" : {
                  "a" : 1,
                  "b" : true,
                  "c" : "some string"
               },
               "start" : 0,
               "type" : "Type1"
            }
         ],
         "name" : "",
         "next_annid" : 1
      },
      "Set2" : {
         "annotations" : [
            {
               "id" : 0,
               "start" : 2,
               "features" : {},
               "type" : "Type2",
               "end" : 8
            }
         ],
         "next_annid" : 1,
         "name" : "Set2"
      }
   },
   "text" : "A simple document"
}
```
