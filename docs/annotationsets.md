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

Annotations can overlap arbitrarily and 

