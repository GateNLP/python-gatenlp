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
