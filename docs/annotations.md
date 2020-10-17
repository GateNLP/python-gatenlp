# Annotations

See also:  [Python Documentation](pythondoc/gatenlp/annotation.html)

Annotations are objects that provide information about a span of text. In `gatenlp` annotations are used to identify tokens, entities, sentences, paragraphs, and other things: unlike in other NLP libraries, the same abstraction is used for everything that is about offset spans in a document. This abstraction is identical to what is used in Java GATE.

Annotations contain the following information:

* start offset (`ann.start`): the offset of the first character of the span
* end offset (`ann.end`): the offset after the last character of the span
* type (`ann.type`): some arbitrary name for the type of offset range represented, e.g. "Token", "Sentence", "Person"
* features (`ann.features`): arbitrary name/value pairs providing the information about the span, where name is a string and value is any JSON-serializable data type. 
* id (`ann.id`): the annotation id identifies the annotation uniquely within the containing [AnnotationSet](annotationsets). 

The normal way to create an annotation is by using the `AnnotationSet` method `add`:

```python
from gatenlp import Document, Annotation
doc = Document("Some test document")
annset = doc.annset()
ann = annset.add(2,4,"Token",{"lemma": "is"})
ann
# Out: Annotation(2,4,Token,id=1,features={'lemma': 'is'})
```

This creates an annotation of type "Token" starting with the character at offset 2 and ending with the character at offset 3 (the end offset is alwyas one after the last character). The annotation gets initialized with a single feature "lemma" which has the value "is". 

Once an annotation has been created, everything but the features is immutable. Trying to e.g. do `ann.start = 12` will raise an exception.

To change or set or remove a feature use the methods provided
by [Features](docs/pythondoc/gatenlp/features.html)

An annotation can also be directly created:
```python
ann2 = Annotation(2,4,"Token",annid=1,features={"lemma": "is"})
ann2
# Out: Annotation(2,4,Token,id=1,features={'lemma': 'is'})
```

However such a "free floating" annotation is probably not of much use and there is no way to add it directly to an annotation set. The method `annset.add_ann(ann)` can be used to add an anntotation that is a copy of `ann`. 

## Annotation span methods

There can be as many annotations for as many arbitrary spans as needed, and they can overlap arbitrarily.  There are several annotation methods which can be used to find out how exactly they overlap or are contained within each other. 

```python
ann_tok1 = annset.add(0,4,"Token")
ann_tok2 = annset.add(5,13,"Token")
ann_all = annset.add(0,13,"Document")
ann_vowel1 = annset.add(1,2,"Vowel")
ann_vowel2 = annset.add(3,4,"Vowel")
```

Annotations have a "length" which is the number of characters annotated, i.e. the length of the annotated span: 

```
assert ann_tok1.length == 4
```


The ordering of annotations is by start offset, then annotation id.

```python
# does one annotation come before the other?
ann_tok1 < ann_tok2
# True
ann_tok1 < ann_vowel1
# True
ann_tok1 < ann_all
# True (annotations added later have a higher annotation id)
```

Checking for overlaps:

```python
ann_tok1.isoverlapping(ann_tok2)
# False
ann_tok1.iscoextensive(ann_tok2)
# False: not the same span
ann_tok1.isoverlapping(ann_vowel1)
# True
ann_tok1.iswithin(ann_all)
# True
ann_tok1.iscovering(ann_vowel2)
# True 
ann_tok1.isbefore(ann_tok2)
# True
ann_tok1.isbefore(ann_tok2, immediately=True)
# False
ann_tok1.gap(ann_tok2)
# 1
```

