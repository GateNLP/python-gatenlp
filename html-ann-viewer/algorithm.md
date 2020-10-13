# Notes about the algorithm


## Creating the spans

* Step 1: build the initial anns4offset datastructure:
  * for each offset one element
  * element is a map with fields "offset" and "anns" which is a set of Setname/Typename/annid strings where 
    a special separator is used instead of "/"
  * undefined elements indicate that no annotation is present at this offset
  * all offsets covered by one or more annotations have the set of annotations stored
  * the element after an annotation, unless already present is set to have the empty list stored (for compression later)
* Step 2: compress the list to only contains an entry where the set/ann changes.
  * After this step, we have an entry for each offset, where a new combination of annotations occurs 
  * a new combination of annotations can be the empty set if an annotation ends
* Step 3: create the actual HTML by iterating over the elements of the compressed set
  * Start with last being the first element, if it does not exist create the empty list
  * Now iterate from the second to the last element and:
  * if we find something, whatever we had ends
    * if the list of annotations in last was empty, a span without annotations ends, create an ordinary span
    * if the list of annotations in last was not empty, annotations were there, create a span with on click callback and bg color
  * after the last element, add the span that remains to the document end  unless we are already there

Optimization: 
* check if we really need a dictionary for the anns4offset array elements: if we do not need the offset, just the set would be better
* !! complex: instead of recreating the anns4offset datastructure from scratch when selecting a type, can we do it incrementally?
  * would still need to re-create the whole HTML 
* We can only update the html if we split into ALL possible spans from the start, then only recolor the spans, but that may be 
  to complex and not actually speed up things that much
* real big documents: ????
