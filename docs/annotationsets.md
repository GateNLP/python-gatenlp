# Annotation Sets

See also: [Python Documentation](pythondoc/gatenlp/annotation_set.html)

Annotation sets group annotations that belong together in some way. How to group annotations is entirely up to the user. 

Annotation sets are identified by names and there can be as many different sets as needed. The annotation set with the empty string as name is called the "default annotation set". There are no strict limitations to annotation set names, but it is recommended that apart from the default set, all names should follow Java or python name conventions. 

Annotation sets are represented by the `AnnotationSet` class and created by fetching a set from the document.


```python
from gatenlp import Document

doc = Document("some document with some text so we can add annotations.")
annset = doc.annset("MySet")
```

Once an annotation set has been created it can be used to create and
add as many annotations as needed to it:


```python
ann_tok1 = annset.add(0,4,"Token")
ann_tok2 = annset.add(5,13,"Token")
ann_all = annset.add(0,13,"Document")
ann_vowel1 = annset.add(1,2,"Vowel")
ann_vowel2 = annset.add(3,4,"Vowel")
```

Annotations can overlap arbitrarily and there are methods to check the overlapping and location relative to each other through the [Annotation](annotations) methods. 

The AnnotationSet instance has methods to retrieve annotations which relate to an annotation span or offset span in some specific way, e.g. are contained in the annotation span, overlap the annotation span or contain the annotation span:


```python
anns_intok1 = annset.within(ann_tok1)
print(anns_intok1)
# AnnotationSet([
#   Annotation(1,2,Vowel,id=3,features=None),
#   Annotation(3,4,Vowel,id=4,features=None)])

anns_intok1 = annset.within(0,4)
print(anns_intok1)
# AnnotationSet([
#   Annotation(0,4,Token,id=0,features=None),
#   Annotation(1,2,Vowel,id=3,features=None),
#   Annotation(3,4,Vowel,id=4,features=None)])
```

    AnnotationSet([Annotation(1,2,Vowel,features=Features({}),id=3), Annotation(3,4,Vowel,features=Features({}),id=4)])
    AnnotationSet([Annotation(0,4,Token,features=Features({}),id=0), Annotation(1,2,Vowel,features=Features({}),id=3), Annotation(3,4,Vowel,features=Features({}),id=4)])


In the example above, the annotation `ann_tok1` which has offsets (0,4) is not 
included in the result of `annset.within(ann_tok1)`: if an annotation is passed to any of these functions, by default that same annotation is not included in the result annotation set. 
This behaviour can be changed by using `include_self=True`. 

## Result Annotation Sets

There are three ways of how one can obtain an annotation set in `gatenlp`:

* From the document, using `annset()` or `annset("name")`: this is how to get a handle to an annotation set that is stored with the document and known by some name (which can be the empty string) . Whenever annotations are added to or deleted from such a set, this modifies what is stored with the document.  Such sets are called "attached". 
* As the result of many of the AnnotationSet methods, e.g. `annset.covering(span)`: such annotation sets are by default immutable: they do not allow to add or delete annotations, but they can be changed to be mutable. Once mutable, annotations can get added or deleted but none of these changes are visible in the document: the set returned from the method is a "*detached*" set. 
* With the `AnnotationSet` constructor: such a set is empty and "detached". 

A "detached" annotation set returned from an AnnotationSet method contains annotations from the original attached set, and while the list of annotations is separate, the annotations themselves are identical to the ones in the original attached set. So if you change features of those annotations, they will modify the annotations in the document. 

In order to get a completely independent copy of all the annotations from a result set (which is a detached set), the method: `clone_anns()` can be used. After this, all the annotations are deep copies of the originals and can be modified without affecting the annotations in the original attached set. 

In order to get a completely independent copy of all the annotations from an original attached set, the method `deepcopy()` can be used.

See examples below under "Accessing Annotations by Type"

## Indexing by offset and type

AnnotationSet objects initially just contain the annotations which are stored in some arbitrary order internally. But as soon any method is used that has to check how the start or end offsets compare between annotations or which require to process annotations in offset order, an index is created internally for accessing annotations in order of start or end offset. Similarly, any method that retrieves annotations by type creates an index to speed up retrieval. Index creation is done automatically as needed. 

Index creation can require a lot of time if it is done for a large corpus of documents. 

## Iterating over Annotations 

Any AnnotationSet can be iterated over: 




```python
annset.add(20,25,"X")
annset.add(20,21,"X")
annset.add(20,27,"X")

for ann in annset:
    print(ann)
```

    Annotation(0,4,Token,features=Features({}),id=0)
    Annotation(0,13,Document,features=Features({}),id=2)
    Annotation(1,2,Vowel,features=Features({}),id=3)
    Annotation(3,4,Vowel,features=Features({}),id=4)
    Annotation(5,13,Token,features=Features({}),id=1)
    Annotation(20,25,X,features=Features({}),id=5)
    Annotation(20,21,X,features=Features({}),id=6)
    Annotation(20,27,X,features=Features({}),id=7)


The default sorting order of annotations is by start offset, then by annotation id. So the end offset is not 
involved in the order, but annotations at the same offset are ordered by annotation id. Annotation ids are always incremented when annotations get added.

The default iterator needs to first created the index for sorting annotations in offset order. If this is not relevant, it is possible to avoid creating the index by using `fast_iter()` which iterates over the annotations in the order they were added to the set. 


```python
for ann in annset.fast_iter():
    print(ann)
```

    Annotation(0,4,Token,features=Features({}),id=0)
    Annotation(5,13,Token,features=Features({}),id=1)
    Annotation(0,13,Document,features=Features({}),id=2)
    Annotation(1,2,Vowel,features=Features({}),id=3)
    Annotation(3,4,Vowel,features=Features({}),id=4)
    Annotation(20,25,X,features=Features({}),id=5)
    Annotation(20,21,X,features=Features({}),id=6)
    Annotation(20,27,X,features=Features({}),id=7)


Annotations can be iterated over in reverse offset order using `reverse_iter()`:


```python
for ann in annset.reverse_iter():
    print(ann)
```

    Annotation(20,27,X,features=Features({}),id=7)
    Annotation(20,21,X,features=Features({}),id=6)
    Annotation(20,25,X,features=Features({}),id=5)
    Annotation(5,13,Token,features=Features({}),id=1)
    Annotation(3,4,Vowel,features=Features({}),id=4)
    Annotation(1,2,Vowel,features=Features({}),id=3)
    Annotation(0,13,Document,features=Features({}),id=2)
    Annotation(0,4,Token,features=Features({}),id=0)


## Accessing Annotations by Type

Each annotation has an annotation type, which can be an arbitrary string, but using something that follows Java or Python naming conventions is recommended. 

To retrieve all annotations with some specific type, use `with_type()`:


```python
anns_vowel = annset.with_type("Vowel")
print(anns_vowel)
```

    AnnotationSet([Annotation(1,2,Vowel,features=Features({}),id=3), Annotation(3,4,Vowel,features=Features({}),id=4)])


The result set is a *detached* and *immutable* annotation set:
    


```python
print(anns_vowel.immutable)
print(anns_vowel.isdetached())

try:
    anns_vowel.add(2,3,"SomeNew")
except:
    print("Cannot add a new annotation")
```

    True
    True
    Cannot add a new annotation


After making the result set mutable, we can add annotations:



```python
anns_vowel.immutable = False
anns_vowel.add(2,3,"SomeNew")
print(anns_vowel)
```

    AnnotationSet([Annotation(1,2,Vowel,features=Features({}),id=3), Annotation(2,3,SomeNew,features=Features({}),id=8), Annotation(3,4,Vowel,features=Features({}),id=4)])


But since the result set is detached, the added annotation does not become part of the original annotation set stored with the document:


```python
print(annset)
```

    AnnotationSet([Annotation(0,4,Token,features=Features({}),id=0), Annotation(0,13,Document,features=Features({}),id=2), Annotation(1,2,Vowel,features=Features({}),id=3), Annotation(3,4,Vowel,features=Features({}),id=4), Annotation(5,13,Token,features=Features({}),id=1), Annotation(20,25,X,features=Features({}),id=5), Annotation(20,21,X,features=Features({}),id=6), Annotation(20,27,X,features=Features({}),id=7)])


In order to add annotations to the set stored with the  document, that set needs to be used directly, not a result set 
obtained from it. Note that if an annotation is added to the original set, this does not affect any result set already obtained:  


```python
annset.add(2,3,"SomeOtherNew")
print(annset)
```

    AnnotationSet([Annotation(0,4,Token,features=Features({}),id=0), Annotation(0,13,Document,features=Features({}),id=2), Annotation(1,2,Vowel,features=Features({}),id=3), Annotation(2,3,SomeOtherNew,features=Features({}),id=8), Annotation(3,4,Vowel,features=Features({}),id=4), Annotation(5,13,Token,features=Features({}),id=1), Annotation(20,25,X,features=Features({}),id=5), Annotation(20,21,X,features=Features({}),id=6), Annotation(20,27,X,features=Features({}),id=7)])


## Overview over the AnnotationSet API




```python
# get the annotation set name
print(annset.name)
```

    MySet



```python
# Get the number of annotations in the set: these two are equivalent
print(annset.size, len(annset))
```

    9 9



```python
# Get the document the annotation set belongs to:
print(annset.document)
```

    Document(some document with some text so we can add annotations.,features=Features({}),anns=['MySet':9])



```python
# But a detached set does not have a document it belongs to:
print(anns_vowel.document)
```

    None



```python
# Get the start and end offsets for the whole annotation set
print(annset.start, annset.end)
# or return a tuple directly
print(annset.span)
```

    0 27
    (0, 27)



```python
# get an annotation by annotation id
a1 = anns_vowel.get(8)
print(a1)

```

    Annotation(2,3,SomeNew,features=Features({}),id=8)



```python
# add an annotation that looks exactly as a given annotation:
# the given annotation itself is not becoming a member of the set
# It gets a new annotation id and a new identity. However the features are shared.
# An annotation can be added multiple times this way:
a2 = annset.add_ann(a1)
print(a2)
a3 = annset.add_ann(a1)
print(a3)

```

    Annotation(2,3,SomeNew,features=Features({}),id=9)
    Annotation(2,3,SomeNew,features=Features({}),id=10)



```python
# Remove an annotation from the set.
# This can be done by annotation id:
annset.remove(a3.id)
# or by passing the annotation to remove
annset.remove(a2)
print(annset)
```

    AnnotationSet([Annotation(0,4,Token,features=Features({}),id=0), Annotation(0,13,Document,features=Features({}),id=2), Annotation(1,2,Vowel,features=Features({}),id=3), Annotation(2,3,SomeOtherNew,features=Features({}),id=8), Annotation(3,4,Vowel,features=Features({}),id=4), Annotation(5,13,Token,features=Features({}),id=1), Annotation(20,25,X,features=Features({}),id=5), Annotation(20,21,X,features=Features({}),id=6), Annotation(20,27,X,features=Features({}),id=7)])



```python
# Check if an annotation is in the set

print("ann_tok1 in the set:", ann_tok1 in annset)
tmpid = ann_tok1.id
print("ann_tok1 in the set, by id:", tmpid in annset)

```

    ann_tok1 in the set: True
    ann_tok1 in the set, by id: True



```python
# Get all annotation type names in an annotation set
print("Types:", annset.type_names)
```

    Types: dict_keys(['Token', 'Document', 'Vowel', 'X', 'SomeOtherNew', 'SomeNew'])



```python

```


```python

```


```python

```
