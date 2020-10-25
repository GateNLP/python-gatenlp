# Document Corpora


Corpora are collections of documents and in GateNLP, there are three classes which represent collections of 
documents:

* Corpus: this is any object that behaves like a list or array of documents and allows to get and set the nth document via `mycorpus[n]` and `mycorpus[n] = doc`. A Python list can thus be used as a Corpus, but GateNLP provides other Corpus classes for getting and saving documents from/to a directory and other storage locations. 
* DocumentSource: this is something that can be used as an iterator over documents. Any iterable of documents can be used as DocumentSource, but GateNLP provides a number of classes to iterate over documents from other sources, like the result of a database query. 
* DocumentDestination: this is something where a document can be added to by invoking the `add` or `append` method. 

Corpus and DocumentSource objects can be processed by an executor (see [Processing](processing))

## JsonLinesFileSource and JsonLinesFileDestination

This document source reads the JSON bdoc representation of a document from each line in an input file and 
produces the corresponding documents. When a gatenlp Document is saved as "json", i.e. in bdoc json format,
all json is in a single line since any newline character gets escaped in the json representation.

This makes it possible to store several documents in a single text file by having one json-serialization 
per row. 


```python
import os
from gatenlp import Document
from gatenlp.corpora import JsonLinesFileDestination, JsonLinesFileSource
from gatenlp.corpora import DirFilesDestination, DirFilesSource, DirFilesCorpus
from gatenlp.corpora import TsvFileSource

# all the example files will be created in "./tmp"
if not os.path.exists("tmp"):
    os.mkdir("tmp")
```


```python
# lets start with a few texts to create documents from
texts = [
    "This is the first text.",
    "Another text.\nThis one has two lines",
    "This is the third document.\nIt has three lines.\nThis line is the last one.\n",
    "And another document."
]

docs = [Document(txt) for txt in texts]

# print the text of the third document (index 2): this shows that the text has three lines:
print(docs[2].text)
# lets create the json representation and print it too - this only occupies one line:
json = docs[2].save_mem(fmt="json")
print(json)
```

    This is the third document.
    It has three lines.
    This line is the last one.
    
    {"annotation_sets": {}, "text": "This is the third document.\nIt has three lines.\nThis line is the last one.\n", "features": {}, "offset_type": "p", "name": ""}



```python
# now lets save the 4 documents to a single JsonLinesFile using the document destination:
# IMPORTANT: the file is only complete once the destination has been closed!
jsfile1 = os.path.join("tmp","jsonlinesfile1.jsonl")
dest1 = JsonLinesFileDestination(jsfile1)
for doc in docs:
    dest1.append(doc)
dest1.close()
```


```python
# lets view the created file: 
with open(jsfile1, "rt") as infp:
    print(infp.read())
```

    {"annotation_sets": {}, "text": "This is the first text.", "features": {}, "offset_type": "p", "name": ""}
    {"annotation_sets": {}, "text": "Another text.\nThis one has two lines", "features": {}, "offset_type": "p", "name": ""}
    {"annotation_sets": {}, "text": "This is the third document.\nIt has three lines.\nThis line is the last one.\n", "features": {}, "offset_type": "p", "name": ""}
    {"annotation_sets": {}, "text": "And another document.", "features": {}, "offset_type": "p", "name": ""}
    



```python
# Another way to use most document destinations is in a "with" block, which has the advantage that the 
# destination will get closed automatically:
jsfile2 = os.path.join("tmp","jsonlinesfile2.jsonl")
with JsonLinesFileDestination(jsfile2) as dest:
    for doc in docs:
        dest.append(doc)
        
with open(jsfile2, "rt") as infp:
    print(infp.read())
```

    {"annotation_sets": {}, "text": "This is the first text.", "features": {}, "offset_type": "p", "name": ""}
    {"annotation_sets": {}, "text": "Another text.\nThis one has two lines", "features": {}, "offset_type": "p", "name": ""}
    {"annotation_sets": {}, "text": "This is the third document.\nIt has three lines.\nThis line is the last one.\n", "features": {}, "offset_type": "p", "name": ""}
    {"annotation_sets": {}, "text": "And another document.", "features": {}, "offset_type": "p", "name": ""}
    



```python
# Now that we have create a jsonlines file, we can use a document source to iterate over the documents in it

for doc in JsonLinesFileSource(jsfile2):
    print(doc)
```

    Document(This is the first text.,features=Features({}),anns=[])
    Document(Another text.
    This one has two lines,features=Features({}),anns=[])
    Document(This is the third document.
    It has three lines.
    This line is the last one.
    ,features=Features({}),anns=[])
    Document(And another document.,features=Features({}),anns=[])


## DirFilesSource, DirFilesDestination, DirFilesCorpus

The DirFilesSource is a document sorce that imports/reads files in a directory or directory tree as one 
iterates over the source. 

The DirFilesDestination is a destination that creates files in a directory as documents get appended to the destination. 

The DirFilesCorpus is a corpus that accesses stored documents in a directory or directory tree when accessing 
the corpus element and stores them back to their file when assigning the corpus element. 

Let's first convert the jsonlines file we have created into a directory corpus. A directory files corpus allows
for several different ways of how to name the files or file paths within the directory. Here we simply use the 
index of the document, i.e. the running number of the document as the base name of the created file:



```python
dir1 = os.path.join("tmp", "dir1")
if not os.path.exists(dir1):
    os.mkdir(dir1)  # The directory for a DirFilesDestination must exist
# The path_from="idx" setting makes the DirFilesCorpus use the running number of the document as 
# the file base name.

with DirFilesDestination(dir1, ext="bdocjs", path_from="idx") as dest:
    for doc in JsonLinesFileSource(jsfile1):
        dest.append(doc)
    

# lets see what the content of the directory is now:
print(os.listdir(dir1))
```

    ['3.bdocjs', '1.bdocjs', '0.bdocjs', '2.bdocjs']


Now that we have a directory with files representing documents, we can open it as 
a document source or corpus.

If we open it as a document source, we can simply iterate over all documents in it:


```python
src2 = DirFilesSource(dir1)
for doc in src2:
    print(doc)
```

    Document(And another document.,features=Features({}),anns=[])
    Document(Another text.
    This one has two lines,features=Features({}),anns=[])
    Document(This is the first text.,features=Features({}),anns=[])
    Document(This is the third document.
    It has three lines.
    This line is the last one.
    ,features=Features({}),anns=[])


If we open it as a document corpus, we can directly access each document as from a list or an array:


```python
corp1 = DirFilesCorpus(dir1)
```


```python
# we can get the length
print("length is:", len(corp1))

# we can iterate over the documents in it:
print("Original documents:")
for doc in corp1:
    print(doc)
    
# but we can also update each element which will save the corresponding document to the original
# file in the directory where it was loaded from. Here we add an annotation and document feature
# to each document in the corpus.
for idx, doc in enumerate(corp1):
    doc.features["docidx"] = idx
    doc.annset().add(0,3,"Type1")
    corp1[idx] = doc  # !! this is what updates the document file in the directory
    
# the files in the directory now contain the modified documents. lets open them again and show them 
# using a dirfiles source:
src3 = DirFilesSource(dir1)
print("Updated documents:")
for doc in src2:
    print(doc)
```

    length is: 4
    Original documents:
    Document(And another document.,features=Features({}),anns=[])
    Document(Another text.
    This one has two lines,features=Features({}),anns=[])
    Document(This is the first text.,features=Features({}),anns=[])
    Document(This is the third document.
    It has three lines.
    This line is the last one.
    ,features=Features({}),anns=[])
    Updated documents:
    Document(And another document.,features=Features({'docidx': 0}),anns=['':1])
    Document(Another text.
    This one has two lines,features=Features({'docidx': 1}),anns=['':1])
    Document(This is the first text.,features=Features({'docidx': 2}),anns=['':1])
    Document(This is the third document.
    It has three lines.
    This line is the last one.
    ,features=Features({'docidx': 3}),anns=['':1])


## TsvFileSource

The TsvFileSource is a document source which initializes documents from the text in some column of a tsv
file and optionally sets document features from other columns of the tsv file. 


```python
# Let's load documents from a tsv file on a web page. This tsv file has three columns and a header line which 
# gives the names "text", "feat1" "feat2" to the columns. 
# We create the documents by fetching the text from column "text" and creating two document features
# with names "f1" and "f2" from the columns "feat1" and "feat2":
tsvsrc = TsvFileSource("https://gatenlp.github.io/python-gatenlp/tsvcorpus_example1.tsv",
                      text_col="text", feature_cols=dict(f1="feat1", f2="feat2"))



for doc in tsvsrc:
    print(doc)
```

    Document(Here is some text. Like with JSON, newlines are escaped:\nHere is another line.,features=Features({'f1': 'fval1', 'f2': 'fval2\n'}),anns=[])
    Document(Another text\nThis one\nhas more\n\nlines.,features=Features({'f1': '11', 'f2': '22\n'}),anns=[])
    Document(And another.,features=Features({'f1': 'a', 'f2': 'b\n'}),anns=[])



```python
# clean up after ourselves
import shutil
shutil.rmtree("tmp")
```
