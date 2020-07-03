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

Many methods of the `AnnotationSet` class return an annotation set which contains a subset of the original set. But what happens if:

* a)  Annotations are added to or removed from that result set? Will that add or remove those annotations to the original set?
* b) Annotations included in that result set get their features changed? Will that modify the annotations in the original set? 



