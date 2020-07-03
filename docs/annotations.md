# Annotations

See also: [Python Documentation](pythondoc/gatenlp.annotation.html)

Annotations are objects that provide information about a span of text. In `gatenlp` annotations are used to identify tokens, entities, sentences, paragraphs, and other things: unlike in other NLP libraries, the same abstraction is used for everything that is about offset spans in a document. This abstraction is identical to what is used in Java GATE.

Annotations contain the following information:

* start offset: the offset of the first character of the span
* end offset: the offset after the last character of the span
* type: some arbitrary name for the type of offset range represented, e.g. "Token", "Sentence", "Person"
* features: arbitrary name/value pairs providing the information about the span, where name is a string and value is any JSON-serializable data type. 
* id: the annotation id identifies the annotation uniquely within the containing [AnnotationSet](annotationsets). 

The normal way to create an annotation is by using the `AnnotationSet` method `add`:

```python
from gatenlp import Document, Annotation
doc = Document("Some test document")
ann = doc.get_annotations().add(2,4,"Token",{"lemma": "is"})
ann
# Out: Annotation(2,4,Token,id=1,features={'lemma': 'is'})
```

This creates an annotation of type "Token" starting with the character at offset 2 and ending with the character at offset 3 (the end offset is alwyas one after the last character). The annotation gets initialized with a single feature "lemma" which has the value "is". 

Once an annotation has been created, everything but the features is immutable. Trying to e.g. do `ann.start = 12` will raise an exception.

To change or set or remove a feature use the methods inherited 
from [FeatureBearer](docs/pythondoc/gatenlp.feature_bearer.html)

An annotation can also be directly created:
```python
ann2 = Annotation(2,4,"Token",annid=1,features={"lemma", "is"})
ann2
# Out: Annotation(2,4,Token,id=1,features={'lemma': 'is'})
```

However such a "free floating" annotation is probably not of much use and there is no way to add it to an annotation set. 