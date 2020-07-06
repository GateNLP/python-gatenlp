# Annotation Sets

See also: [Python Documentation](pythondoc/gatenlp.annotation_set.html)

Annotation sets group annotations that belong together in some way. This is entirely up to the user. 

Annotation sets are identified by names and there can be as many different sets as needed. The annotation set with the empty string as name is called the "default annotation set". There are no strict limitations to annotation set names, but it is recommended that apart from the default set, all names should follow Java or python name conventions. 

Annotation sets are represented by the `AnnotationSet` class and created by fetching from the document. 

```python
from gatenlp import Document

doc = Document("some document")
annset = doc.get_annotations("MySet")
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
# AnnotationSet([
#   Annotation(1,2,Vowel,id=3,features=None),
#   Annotation(3,4,Vowel,id=4,features=None)])
anns_intok1 = annset.within(0,4)
# AnnotationSet([
#   Annotation(0,4,Token,id=0,features=None),
#   Annotation(1,2,Vowel,id=3,features=None),
#   Annotation(3,4,Vowel,id=4,features=None)])
```

In the example above, the annotation `ann_tok1` which has offsets (0,4) is not 
included in the result of `annset.within(ann_tok1)`: if an annotation is passed to any of these functions, by default that same annotation is not included in the result annotation set. 
This behaviour can be changed by using `include_self=True`. 

## Result Annotation Sets

There are three ways of how one can obtain an annotation set in `gatenlp`:

* From the document, using `get_annotations()` or `get_annotations("name")`: this is how to get a handle to an annotation set that is stored with the document and known by some name (which can be the empty string) . Whenever annotations are added to or deleted from such a set, this modifies what is stored with the document.  Such sets are called "attached". 
* As the result of many of the AnnotationSet methods, e.g. `annset.covering(span)`: such annotation sets are by default immutable: they do not allow to add or delete annotations, but they can be changed to be mutable. Once mutable, annotations can get added or deleted but none of these changes are visible in the document: the set returned from the method is a "*detached*" set. 
* With the `AnnotationSet` constructor: such a set is empty and "detached". 

A "detached" annotation set returned from an AnnotationSet method contains annotations from the original attached set, and while the list of annotations is separate, the annotations themselves are identical to the ones in the original attached set. So if you change features of those annotations, they will modify the annotations in the document. 

In order to get a completely independent copy of all the annotations from a result set (which is a detached set), the method: `clone_anns()` can be used. After this, all the annotations are copies of the originals and can be modified without affecting the annotations in the original attached set. 

In order to get a completely independent copy of all the annotations from an original attached set, the method `deepcopy()` can be used. 


