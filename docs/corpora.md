# Document Corpora


Corpora are collections of documents and in GateNLP, there are three classes which represent collections of 
documents:

* Corpus: this is any object that behaves like a list or array of documents and allows to get and set the nth document via `mycorpus[n]` and `mycorpus[n] = doc`. A Python list can thus be used as a Corpus, but GateNLP provides other Corpus classes for getting and saving documents from/to a directory and other storage locations. 
* DocumentSource: this is something that can be used as an iterator over documents. Any iterable of documents can be used as DocumentSource, but GateNLP provides a number of classes to iterate over documents from other sources, like the result of a database query. 
* DocumentDestination: this is something where a document can be added to by invoking the `add` or `append` method. 

Corpus and DocumentSource objects can be processed by an executor (see [Processing](processing))
