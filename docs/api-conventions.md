# API Naming Conventions

To make using the Python API easier to use, we try to use consisten naming between
classes and functions. 

This is a list of naming conventions used so far:

* File/path names: usually represented as the platform-specific string representation of the file. In some cases,
  the string will get interpreted as a URL if it starts with "http://" or "https://" - in those cases a
   parsed URL or a pathlib Path object can be used to make explicity if a local path or a URL should be used.
* Parameter name `annspec`: an "annotation specification" used to specify which annotation types from which annotation sets should
  be used for some action. This can be a string (all annotations from the set with that name) or a list. Each element in the list
  can be a string (all annotations from the annotationset with that name) or a tuple. The first element of the tuple is the 
  annotation set name, the second element of the tuple is either a string (the name of the annotation type to use from the given set)
  or a list of strings (several annotation types to use from that set). 
