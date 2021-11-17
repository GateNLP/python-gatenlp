# StringRegexAnnotator Reference

The `StringRegexAnnotator` annotator can be used to define regular-expression based rules for 
annotating documents. 

A _file_ or _string_ with rules must have the following format:

* empty lines are ignored
* lines starting with "#" or "//" are comments and ignored
* lines starting with "|" or "+" are pattern lines 
* lines starting with a comma-separated list of integers followed by "=>" are action lines
* each rule consists of one or more pattern lines followed by one or more rule lines
* a previous rule ends whenever a new patten line is encountered 
* a line that starts with a name followed by an equal sign (e.g. "year=[0-9]{4}") is a macro definition
* a pattern line which contains a name enclosed in double braces (e.g. "{{year}}") has that name replaced by
  the value assigned in a previous macro. If the name is not known there is no error or replacement and the string 
  is used unchanged. 
  
## Macros

Macros can be used to build complex pattern from simpler building blocks by defining a name in an assignment line and 
later using that name in any pattern line of any rule as often as needed. Names are replaced recursively, i.e. the pattern
assigned to a name can itself contain a previously defined name placeholder.

Example:
```
# define a pattern for a 4 digit year, 2 digit month and 2 digit day
year=19[0-9]{2}|20[0-9]{2}
month=0[0-9]|10|11|12
day=[02][0-9]|3[01]

# use the names for the ISO date
isodate={{year}}-{{month}}-{{day}}

# use the names for traditional date
olddate={{day}}/{{month}}/{{year}}

# define a rule to find either an iso date or a traditional date
|{{isodate}}
|{{olddate}}
0 => Date
```

## Pattern lines

Any line that starts with a vertical bar "|" is a pattern line that represents one of several, or the only alternative. 
If there are several lines each starting with a vertical bar, the final pattern is created as a pattern where each 
of the patterns from each line are enclosed in a non-binding group and the final pattern is the list of each of those 
patterns as alternatives. 

Example:
```
|[a-z]
|[0-9]
|[_$]
0 => Match
```

For this rule, the final pattern used is "(?:[a-z])|(?:[0-9])|(?:[_$])"

Any line that starts with a plus "+" is a pattern line that represents one of several, or the only part of a pattern 
that is a concatenation of several parts. Each line starting with "+" gets concatenated (after removing leading and trailing whitespace) 
to the previous line. If a "+" is the very first line for a rule, it gets treated like the firs "|" line. 

Example:
```
|[a-z]
+[0-9]
+[_$]
0 => Match
```

For this rule, final pattern used is "(?:[a-z][0-9][_$])"

## Action lines

Any line that starts with a comma, separated list of one or more group numbers, followed by "=>", followed by the name of an annotation type name
is an action line. The list of group numbers represents for which captured groups in the regular expression an annotation should get created and 
the annotation type name is used for those annotations. After the annotation type name there can be one or more comma separated feature assignments.
There can be as many action lines as needed.

Each feature assignment is of the form `featurename=featurevalue` where the feature value is either a python constant or one of the predefined variables 
`G0`, `G1` etc. When a match occurs and an annotation is created with the given annotation type name, the given features are also added to the annotation,
with either the constant values or the variables `Gn` replaced with the text matched by the corresponding capturing group `n`. 
It is a runtime error if a group variable is used for which there is no corresponding capturing group in the match.  Group number 0 by convention is always 
referring to the whole regular expression.

Example
```
|([0-9]{4})-([0-9]{2})-([0-9]{2})
0 => Date date=G0, year=G1, month=G2, day=G3
1 => Year date=G0, year=G1, month=G2, day=G3
2 => Month date=G0, year=G1, month=G2, day=G3
3 => Day date=G0, year=G1, month=G2, day=G3
```

This rule would create 4 annotations for each date that matches: one with annotation type "Date" with the span of the whole match, another with 
annotation type "Year" and the span correspning to the first capturing group (the part of the pattern enclosed in the first parentheses), another
with annotation type "Month" for the span corresponding to the second capturing group etc. All annotations also get 4 features with the corresponding string 
of those spans assigned.

## Creating the StringRegexAnnotator

The `StringRegexAnnotator` has the following initialization parameters:

* `source`: the source of the rules, either a file path, or a string, or a list of pre-created rules
* `source_fmt`: the format of the `source`, one of "file" (default), "string" or "rule-list"
* `outset_name`: the name of the annotation set where the annotations created for matches will be added
* `annset_name`: the name of the annotation set that contains the annotations used for `containing_type`, `start_type`, `end_type` or `split_type` (see below)
* `containing_type`: if this is specified (not None), then the matching will only be performed on spans covered by annotations of that type in the document. Otherwise
  matching is performed on the whole document
* `list_features`: a dictionary of features, these features will get added to all annotations created for a match, any features specified in an action line for 
  a rule are added to those features and override them. 
* `skip_longest`: if True, the next match is searched after the end of the longest previous match(es). Otherwise the next match is searched from the next offset
  after the start of the previous match(es). 
* `longest_only`: if True, only annotate for the longest match(es) at each position, otherwise annotate all matches (subject to the `select_rules` parameter)
* `select_rules`: one of "all", "first", "last": for which of all matching rules to perform the action(s) and create annotations
* `regex_module`: one of "re" (default Python regular expression module) or "regex" alternate module which supports additional featires, e.g. unicode character class
  names. In order to use "regex", the Python "regex" package must be installed. 
* `start_type`: the annotation type of annoations which are used to determine valid start offsets for matches. If this is specified, all annotations with this type
  are retrieved from the document and any match of any rule is only considered if it starts at an offset where one of these annotations starts as well. If not specified
  (None), there is no limitation of start offsets. 
* `start_type`: the annotation type of annotations which are used to determine valid end offsets for matches. If not specified (None) there is no limitation of end
  offsets. 
* `split_type`: the annotation type of annotations which identify spans which contain some kind of split. No match may overlap with any such span, i.e. matches 
  cannot cross split spans. If not specified (None), matches are not restricted by split spans. 
  
Rules may get loaded from a source when the `StringRegexAnnotator` instance is created but it is not required. Instead the method `append` can be used 
one or more times after creation to load rules from one or more sources. The `append` method has parameters `source`, `source_fmt` and `list_features` with 
the same meaning as for the init parameters. 




