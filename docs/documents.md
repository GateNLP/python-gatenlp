# Documents
 
 Documents represent the text of the document plus an arbitrary number of annotations organized in an arbitrary number of named annotation sets plus an arbitrary number of document features. 
 
 Documents can be created by directly creating them:
 
 ```python
 doc = Document("this is some document")
 ```
 
 Documents can also be loaded from some supported document format using the `Document.load` method:
 
 ```python
 doc = Document.load("mydoc.bdocjs")  # load from Bdoc JSON format
 ```
 
 All the document formats supported by the GATE plugin [Format: Bdoc](https://github.com/GateNLP/gateplugin-Format_Bdoc) can also be loaded and saved in `gatenlp`
 
 To save a document, use the `save` method of the instance:
 
 ```python
 doc = Document("some document")
 doc.save("mydoc.bdocjs")
 ```
 
 