# Processing


GateNLP does not limit how documents are stored in collections, iterated over, functions applied to the 
documents to modify them etc.

However, GateNLP provides a number of abstractions to help with this in an organized fashion:

* Corpus, DocumentSource, DocumentDestination: this is how collections of documents which can be read/written, 
  read only, or written only are represented in GateNLP. See [Corpora](corpora).
* Annotator: an annotator is something that processes a document and returns the processed document. Most 
  annotators simple return the modified document but GateNLP abstractions also allow to return None to indicate
  filtering a document or a list of documents (e.g. for splitting up documents)
  Any Python callable can be used as an Annotator but GateNLP annotators in addition may implement the methods
  `start` (to perform some start of corpus processing), `finish` (to perform some end of corpus processing and
  return some over-the-corpus result) and `reduce` (to merge several partial over-the corpus results from parallel 
  processing into a single result). 
* Pipeline: a special annotator the encapsulates several annotators. When the pipeline is run on a document, 
  all the contained annotators are run in sequence. 
* Executor: an object that runs some Annotator on a corpus or document source and optionally stores the results
  back into the corpus or into a document destination
  
  
## Annotators

Anny callable that takes a document and returns that document can act as an annotator. Note that an annotator
usually modifies the annotations or features of the document it receives. This happens in place, so the annotator would not have to return the document. However, it is a convention that annotators always return the document that got modified to indicate this to downstream annotators or document destinations. 

If an annotator returns a list, the result of processing is instead the documents in the list which could be none, or more than one. This convention allows a processing pipeline to filter documents or generate several documents from a single one. 

Lets create a simple annotator as a function and apply it to a corpus of documents which in the simplest form is just a list of documents:



```python
import os
from gatenlp import Document
from gatenlp.processing.executor import SerialCorpusExecutor
```


```python
def annotator1(doc):
    doc.annset().add(2,3,"Type1")
    return doc

texts = [
    "Text for the first document.",
    "Text for the second document. This one has two sentences.",
    "And another one.",
]

corpus = [Document(txt) for txt in texts]

# everything happens in memory here, so we can ignore the returned document
for doc in corpus:
    annotator1(doc)
    
for doc in corpus:
    print(doc)


    
```

    Document(Text for the first document.,features=Features({}),anns=['':1])
    Document(Text for the second document. This one has two sentences.,features=Features({}),anns=['':1])
    Document(And another one.,features=Features({}),anns=['':1])


### Annotator classes

When scaling up, annotators become more complex, processing gets more complex, a corpus does not fit into memory any more and so on. For this reason, GateNLP has abstractions which simplify processing in those situations. 

Annotators as classes always must implement the `__call__` special method so that an instance of the class can be used just like a function. In addition Annotator classes can also implement the following methods:

* `start`: this gets automatically invoked by an "Executor"  when processing over a set of documents starts and
  before the first document is processed
* `finish`: this gets automatically invoked by an "Executor" after all documents have been processed and may return an over-the-corpus result
* `reduce`: this gets automatically invoked by any multi-processing "Executor", passing on the results returned by `finish` for each process and passing back the combined results over all processes. 

The result of processing a corpus returned by the executor is whatever is returned by the finish method for a single process execution or what is returned by the reduce method for multiprocessing. (NOTE: multiprocessing executors are not implemented yet!)


```python

```
