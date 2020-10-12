# CHANGES

## Version 0.9

* Several renames of API methods again:
  * Annotation: boolean methods renamed to isxxx(), e.g. `ann1.within(ann2)` renamed to `ann1.iswithin(ann2)`
  * AnnotationSet: some methods are now properties: `size`, `length` 
  * AnnotationSet: method `type(...)` renamed to `with_type(...)`

## Version 0.8

* Breaking change: `annset.add(..)` now returns the annotation, not just 
  the annotation id of the new annotation. This is more useful and getting
  the id from the annotation is just `ann.id` while getting the annotation
  from the annid is more involved. 
* Breaking change: AnnotationSet methods where the annotation passed on would 
  get included in the result set because of the offset range, by default now
  exclude that annotation. So `annset.within(ann1)` does not contain `ann1`
  anymore, although `ann1` obviously satisfies the `within` criterion. 
  This can be disabled by passing `include_self=True` if necessary. 


