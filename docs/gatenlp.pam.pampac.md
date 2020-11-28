<a name="gatenlp.pam.pampac"></a>
# gatenlp.pam.pampac

Module for PAMPAC (Pattern Matching wit PArser Combinators) which allows to create parsers that can match
patterns in annotations and text and carry out actions if a match occurs.

NOTE: this implementation has been inspired by https://github.com/google/compynator

<a name="gatenlp.pam.pampac.Location"></a>
## Location Objects

```python
class Location()
```

A ParseLocation represents the next location in the text and annotation list where a parser will try to
match, i.e. the location after everything that has been consumed by the parser so far.

The text offset equal to the length of the text represent the EndOfText condition and the annotation index
equal to the length of the annotation list represents the EndOfAnns condition.

<a name="gatenlp.pam.pampac.Location.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(text_location=0, ann_location=0)
```

Create a parser location.

**Arguments**:

- `text_location` - the next text offset from which on to parse.
- `ann_location` - the next annotation index from which on to parse.

<a name="gatenlp.pam.pampac.Result"></a>
## Result Objects

```python
class Result()
```

Represents an individual parser result. A successful parse can have any number of parser results which
are alternate ways of how the parser can match the document.

<a name="gatenlp.pam.pampac.Result.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(data=None, location=None, span=None)
```

Create a parser result.

**Arguments**:

- `data` - the data associated with the result, this can be a single item or a list of items.
  Each item must be either a dictionary that describes an individual match or None.
- `location` - the location where the result was matched, i.e. the location *before* matching was done.
- `span` - the span representing the start and end text offset for the match

<a name="gatenlp.pam.pampac.Result.data4name"></a>
#### data4name

```python
 | data4name(name)
```

Return a list of data dictionaries with the given name.

<a name="gatenlp.pam.pampac.Failure"></a>
## Failure Objects

```python
class Failure()
```

Represents a parse failure.

<a name="gatenlp.pam.pampac.Failure.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(message=None, parser=None, location=None, causes=None, context=None)
```

Create a Failure instance.

**Arguments**:

- `message` - the message to describe the parse failure.
- `parser` _str_ - the class name of the parser
- `location` - the location at which the parser failed.
- `causes` - another failure instance or a list of other failure instances which
  can be used to describe the failure of nested parsers in more detail
- `context` - the context at the point of failure. This is stored as a reference so
  the context should not get modified after the failure is constructed.

<a name="gatenlp.pam.pampac.Failure.issuccess"></a>
#### issuccess

```python
 | issuccess()
```

Method for success and failure results which indicates if we have a success or failure.

**Returns**:

  False

<a name="gatenlp.pam.pampac.Failure.describe"></a>
#### describe

```python
 | describe(indent=4, level=0)
```

Return a string with information about the failure.

**Arguments**:

- `indent` - number of characters to indent for each recursive failure.
- `level` - recursive level of failure
  

**Returns**:

  String with information about the failure

<a name="gatenlp.pam.pampac.Success"></a>
## Success Objects

```python
class Success(Iterable,  Sized)
```

Represents a parse success as a (possibly empty) list of result elements.

Each success is a list of result elements, and each result element contains a list
of matching data. A result represents a match at the top/outermost level of a parser.
A parser that is made of sub parsers and sub-sub-parsers returns one or more matches
over all the different ways how those sub-parsers can match at a specific location,
and each result contains a result element for all the named sub- and sub-sub-parsers
the main parser is made of.

<a name="gatenlp.pam.pampac.Success.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(results, context)
```

Create a Success instance.

**Arguments**:

- `results` - a result or a list of results which may be empty
- `context` - the context used when parsing that result. A reference to the context is stored
  so the context may change after the result has been produced if it is used for more
  parsing.

<a name="gatenlp.pam.pampac.Success.issuccess"></a>
#### issuccess

```python
 | issuccess()
```

Method for success and failure results which indicates if we have a success or failure.

**Returns**:

  True

<a name="gatenlp.pam.pampac.Success.pprint"></a>
#### pprint

```python
 | pprint(file=None)
```

Pretty print the success instance to the file or stdout if no file is specified.

**Arguments**:

- `file` - open file handle for use with print.

<a name="gatenlp.pam.pampac.Success.select_result"></a>
#### select\_result

```python
 | @staticmethod
 | select_result(results, matchtype="first")
```

Return the result described by parameter matchtype.

If "all" returns the whole list of matches.

**Arguments**:

- `results` - list of results to select from
- `matchtype` - one of  "first", "shortest", "longest", "all".
  If there is more than one longest or shortest
  result, the first one of those in the list is returned.
  

**Returns**:

  the filtered result or all results

<a name="gatenlp.pam.pampac.Success.result"></a>
#### result

```python
 | result(matchtype="first")
```

Return the result described by parameter matchtype. If "all" returns the whole list of matches.

**Arguments**:

- `matchtype` - one of  "first", "shortest", "longest", "all".
  If there is more than one longest or shortest
  result, the first one of those in the list is returned.
  

**Returns**:

  the filtered result or all results

<a name="gatenlp.pam.pampac.Context"></a>
## Context Objects

```python
class Context()
```

Context contains data and refers to data for carrying out the parse.

A context contains a reference to the document being parsed, the list of annotations to use,
the start and end text offsets the parsing should be restricted to, the output annotation set
to use, the maximum recursion depth and a data structure for memoization.

All these fields are immutable, i.e. the references stored do not usually change during parsing or
when Pampac executes rules on a document. However, all the referenced data apart from start and
end may change.

<a name="gatenlp.pam.pampac.Context.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(doc, anns, start=None, end=None, outset=None, memoize=False, max_recusion=None)
```

Initialize a parse context.

**Arguments**:

- `doc` - the document which should get parsed
- `anns` - an iterable of annotations to use for the parsing
- `start` - the starting text offset for the parse
- `end` - the ending text offset for the parse
- `outset` - an annotation set for where to add any new annotations in an action
- `memoize` - If memoization should be used (NOT YET IMPLEMENTED)
- `max_recusion` - the maximum recursion depth for recursive parse rules (NOT YET IMPLEMENTED)

<a name="gatenlp.pam.pampac.Context.annset"></a>
#### annset

```python
 | @property
 | annset()
```

Return the annotations as a set.

**Returns**:

  annotations as a detached immutable AnnotationSet

<a name="gatenlp.pam.pampac.Context.get_ann"></a>
#### get\_ann

```python
 | get_ann(location)
```

Return the ann at the given location, or None if there is none (mainly for the end-of-anns index).

**Returns**:

  annotation or None

<a name="gatenlp.pam.pampac.Context.nextidx4offset"></a>
#### nextidx4offset

```python
 | nextidx4offset(location, offset, next_ann=False)
```

Return the index of the next annotation that starts at or after the given text offset.
If no such annotation exists the end of annotations index (equal to length of annotations) is returned.

**Arguments**:

- `location` - current location, the annotation is searched from the annotation index following the one in the
  current location
- `offset` - offset to look for
- `next_ann` - if True, always finds the NEXT annotation after the one pointed at with the current location.
  If false keeps the current one if it is still the next one.
  

**Returns**:

  annotation index

<a name="gatenlp.pam.pampac.Context.inc_location"></a>
#### inc\_location

```python
 | inc_location(location, by_offset=None, by_index=None)
```

Return a new location which represents the given location incremented by either the given number of index
count (usually 1), or by the given offset length. Only one of the by parameters should be specified.

If the update occurs by offset, then the annotation index is updated to that of the next index with
a start offset equal or larger than the updated text offset.  This may be the end of annotations index.
If the text offset hits the end of text offset, the annotation index is set to the end of annotations index.

If the update occurs by index, then the text offset is updated to the offset corresponding to the end offset
of the annotation, if there is one.


**Arguments**:

  location:
- `by_offset` - the number of text characters to increment the text offset by
- `by_index` - the number of annotations to increment the index by
  

**Returns**:

  new location

<a name="gatenlp.pam.pampac.Context.update_location_byoffset"></a>
#### update\_location\_byoffset

```python
 | update_location_byoffset(location)
```

Update the passed location so that the annotation index is updated by the text offset: all annotations are
skipped until the start offset of the annotation is at or past the text offset.

**Arguments**:

- `location` - the location to update
  

**Returns**:

  a new location with the annotation index updated

<a name="gatenlp.pam.pampac.Context.update_location_byindex"></a>
#### update\_location\_byindex

```python
 | update_location_byindex(location)
```

Update the passed location from the annotation index and make sure it points to the end of the current
annotation or the end of the document.

**Arguments**:

- `location` - the location to update
  

**Returns**:

  a new location with the text offset updated

<a name="gatenlp.pam.pampac.Context.at_endoftext"></a>
#### at\_endoftext

```python
 | at_endoftext(location)
```

Returns true if the location represents the end of text location

**Arguments**:

- `location` - location
  

**Returns**:

  True if we are at end of text

<a name="gatenlp.pam.pampac.Context.at_endofanns"></a>
#### at\_endofanns

```python
 | at_endofanns(location)
```

Returns true if the location represents the end of anns location

**Arguments**:

- `location` - location
  

**Returns**:

  True if we are at end of anns

<a name="gatenlp.pam.pampac.PampacParser"></a>
## PampacParser Objects

```python
class PampacParser()
```

A Pampac parser, something that takes a context and returns a result.
This can be used to decorate a function that should be used as the parser,
or for subclassing specific parsers.

When subclassing, the method `parse(location, context)`  must be overriden!

All parsers are callables where the `__call__` method has the same signature as the
`match` method. So `SomeParser(...)(doc, anns)` is the same as `SomeParser(...).match(doc, anns)`

<a name="gatenlp.pam.pampac.PampacParser.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(parser_function)
```

Create a parser from the given function.

**Arguments**:

- `parser_function` - the function to wrap into a parser.

<a name="gatenlp.pam.pampac.PampacParser.parse"></a>
#### parse

```python
 | parse(location, context)
```

Invoking the parser function. This invokes the wrapped function for the root PampacParser
class and should be overriden/implemented for PampacParser subclasses.

**Arguments**:

- `location` - where to start parsing
- `context` - the parsing context
  

**Returns**:

  Success or Failure

<a name="gatenlp.pam.pampac.PampacParser.match"></a>
#### match

```python
 | match(doc, anns=None, start=None, end=None, location=None)
```

Runs the matcher/parser on the given document and the given annotations.

Annotations may be empty in which case only matching on text makes sense.

**Arguments**:

- `doc` - the document to run matching on.
- `anns` - (default: None) a set or Iterable of annotations. If this is a list or Iterable, the annotations
  will get matched in the order given. If it is a set the "natural" order of annotations used
  by the annotation set iterator will be used.
- `start` - the minimum text offset of a range where to look for matches. No annotations that start before
  that offset are included.
- `end` - the maximum text offset of a range where to look for matches. No annotation that ends after that
  offset and not text that ends after that offset should get included in the result.
  

**Returns**:

  Success or Failure

<a name="gatenlp.pam.pampac.PampacParser.call"></a>
#### call

```python
 | call(func, onfailure=None)
```

Returns a parser that is equivalent to this parser, but also calls the given function if there is success.

**Arguments**:

- `func` - the function to call on the success. Should take the success object and arbitrary kwargs.
  context and location are kwargs that get passed.
- `onfailure` - the function to call on failure. Should take the failure object and arbitrary kwargs.
  context and location are kwargs that get passed.
  

**Returns**:


<a name="gatenlp.pam.pampac.PampacParser.__or__"></a>
#### \_\_or\_\_

```python
 | __or__(other)
```

Binary Or via the `|` operator.

This allows to write `Parser1(..) | Parser2(..)` instead of `Or(Parser1(..), Parser2(...))`

**Arguments**:

- `other` - the other parser
  

**Returns**:

  A parser that succeeds if either this or the other parser succeeds.

<a name="gatenlp.pam.pampac.PampacParser.__rshift__"></a>
#### \_\_rshift\_\_

```python
 | __rshift__(other)
```

Binary Seq via the `>>` operator.

This allows to write `Parser1(..) >> Parser2(..)` instead of `Seq(Parser1(..), Parser2(...))`

**Arguments**:

- `other` - the other parser
  

**Returns**:

  A parser that succeeds if this parser succeeds and then the other parser succeeds
  after it.

<a name="gatenlp.pam.pampac.PampacParser.__and__"></a>
#### \_\_and\_\_

```python
 | __and__(other)
```

Binary And via the `&` operator.

This allows to write `Parser1(..) & Parser2(..)` instead of `And(Parser1(..), Parser2(...))`

**Arguments**:

- `other` - the other parser
  

**Returns**:

  A parser that succeeds if this parser and the other parser both succeed at the same location.

<a name="gatenlp.pam.pampac.PampacParser.__xor__"></a>
#### \_\_xor\_\_

```python
 | __xor__(other)
```

Binary All via the `^` operator.

This allows to write `Parser1(...) ^ Parser2(...)` instead of `All(Parser1(...), Parser2(...))`

NOTE: `a ^ b ^ c` is NOT the same as All(a,b,c) as the first will fail if b fails but the second will
still return `a ^ c`

**Arguments**:

- `other` - the other parser
  

**Returns**:

  Returns if this and the other parser succeeds at the current location and returns the
  union of all results.

<a name="gatenlp.pam.pampac.PampacParser.where"></a>
#### where

```python
 | where(predicate, take_if=True)
```

Return a parser that only succeeds if the predicate is true on at least one result of
a success of this parser.

**Arguments**:

- `predicate` - the predicate to call on each result which should accept the result and arbitrary
  keyword arguments. The kwargs `context` and `location` are also passed. The predicate
  should return true if a result should get accepted.
- `take_if` - if False the result is accepted if the predicate function returns False for it
  

**Returns**:

  Success with all the results that have been accepted or Failure if no result was accepted

<a name="gatenlp.pam.pampac.PampacParser.repeat"></a>
#### repeat

```python
 | repeat(min=1, max=1)
```

Return a parser where the current parser is successful at least `min` and at most `max` times.

`Parser1(...).repeat(min=a, max=b)` is the same as `N(Parser1(...), min=a, max=b)`

NOTE: this is also the same as `Parser1(...) * (a, b)`

**Arguments**:

- `min` - minimum number of times the parser must be successful in sequence
- `max` - maximum number of times the parser may be successfull in sequence
  

**Returns**:

  Parser to match this parser min to max times.

<a name="gatenlp.pam.pampac.PampacParser.__mul__"></a>
#### \_\_mul\_\_

```python
 | __mul__(n)
```

Return a parser where the current parser is successful n times.

If n is a tuple (a,b)
return a parser where the current parser is successful a minimum of a and a maximum of b times.

`Parser1(...) * (a,b)` is the same as `N(Parser1(...), min=a, max=b)`

**Arguments**:

- `n` - either an integer used for min and max, or a tuple (min, max)
  

**Returns**:

  Parser to match this parser min to max times.

<a name="gatenlp.pam.pampac.PampacParser.within"></a>
#### within

```python
 | within(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is within any annotation
that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match within a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.notwithin"></a>
#### notwithin

```python
 | notwithin(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is not within any annotation
that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match if not within a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.coextensive"></a>
#### coextensive

```python
 | coextensive(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is coextensive with
any annotation that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match when coextensive with a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.notcoextensive"></a>
#### notcoextensive

```python
 | notcoextensive(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is not coextensive
with any annotation
that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match if not coextensive with a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.overlapping"></a>
#### overlapping

```python
 | overlapping(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is overlapping with
any annotation that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match overlapping with a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.notoverlapping"></a>
#### notoverlapping

```python
 | notoverlapping(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is not overlapping
within any annotation
that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match if not overlapping with a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.covering"></a>
#### covering

```python
 | covering(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is covering any annotation
that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match if there is a covering matching annotation

<a name="gatenlp.pam.pampac.PampacParser.notcovering"></a>
#### notcovering

```python
 | notcovering(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is not covering
any annotation
that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match if not covering a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.at"></a>
#### at

```python
 | at(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is starting
at the same offset as an annotation
that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match if starting with a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.notat"></a>
#### notat

```python
 | notat(type=None, features=None, features_eq=None, text=None, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is not starting
with any annotation
that matches the given properties.

NOTE: all the annotations matched in any of the results of this parser are excluded from
the candidates for checking this constraint!

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match if not starting with a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.before"></a>
#### before

```python
 | before(type=None, features=None, features_eq=None, text=None, immediately=False, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is before any annotation
that matches the given properties.

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `immediately` - limit checking to annotations that start right after the end of the current match
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match (immediately) before a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.notbefore"></a>
#### notbefore

```python
 | @support_annotation_or_set
 | notbefore(type=None, features=None, features_eq=None, text=None, immediately=False, matchtype="first")
```

Parser that succeeds if there is a success for the current parser that is not before any annotation
that matches the given properties.

**Arguments**:

- `type` - as for AnnMatcher
- `features` - as for AnnMatcher
- `features_eq` - as for AnnMatcher
- `text` - as for AnnMatcher
- `immediately` - limit checking to annotations that start right after the end of the current match
- `matchtype` - matchtype to use for filtering
  

**Returns**:

  Parser modified to only match if not (immediately) before a matching annotation

<a name="gatenlp.pam.pampac.PampacParser.lookahead"></a>
#### lookahead

```python
 | lookahead(other)
```

Return a parser that only matches the current parser if the given parser can be matched
afterwards.

The match of the given parser is not part of the success and does not increment the
next parsing location.

**Arguments**:

- `other` - a parser that must match after this parser but the match is discarded.
  

**Returns**:

  a parser that mast be followed by a match of the other parser

<a name="gatenlp.pam.pampac.Lookahead"></a>
## Lookahead Objects

```python
class Lookahead(PampacParser)
```

A parser that succeeds for a parser A only if another parser B succeeds right after it.
However the success of parser B is discarded and does not influence the success nor the
next parse location.

If there is more than one result for the success of the parser A, then the result is only
included in the success if the lookahead parser matches and there is only overall success
if at least one result remains. This also depends on the matchtype.

<a name="gatenlp.pam.pampac.Lookahead.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(parser, laparser, matchtype="first")
```

Create a Lookahead parser.

**Arguments**:

- `parser` - the parser for which to return a success or failure
- `laparser` - the parser that must match after the first parser, but it's success is discarded.
- `matchtype` - which matches to include in the result, one of "first", "longest", "shortest", "all".

<a name="gatenlp.pam.pampac.Filter"></a>
## Filter Objects

```python
class Filter(PampacParser)
```

Select only some of the results returned by a parser success, call the predicate function on each to check.
This can also be used to check a single result and decide if it should be a success or failure.

<a name="gatenlp.pam.pampac.Filter.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(parser, predicate, take_if=True, matchtype="first")
```

Invoke predicate with each result of a successful parse of parser and return success with the remaining
list. If the remaining list is empty, return Failure.

**Arguments**:

- `parser` - the parser to use
- `predicate` - the function to call for each result of the parser success
- `take_if` - if True takes if predicate returns True, otherwise if predicate returns false
- `matchtype` - how to choose among all the selected results

<a name="gatenlp.pam.pampac.Call"></a>
## Call Objects

```python
class Call(PampacParser)
```

A parser that calls a function on success (and optionally on failure).

This parser is identical to the original parser but calls the given function
on success. The function must accept the success instance and arbitrary keyword arguments.
The kwargs `context`, `location`, `name` and `parser` are passed on.

If the `onfailure` parameter is not none, this is a function that is called on Failure with the
Failure instance and the same kwargs.

The parsing result of this parser is the same as the parsing result of the original parser.

<a name="gatenlp.pam.pampac.Call.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(parser, func, onfailure=None)
```

Create a Call parser.

**Arguments**:

- `parser` - the original parser to use
- `func` - the function to call if the original parser returns success
- `onfailure` - the function to call if the original parser returns failure

<a name="gatenlp.pam.pampac._AnnBase"></a>
## \_AnnBase Objects

```python
class _AnnBase(PampacParser)
```

Common base class with common methods for both Ann and AnnAt.

<a name="gatenlp.pam.pampac._AnnBase.gap"></a>
#### gap

```python
 | gap(min=0, max=0)
```

Return a parser which only matches self if the next annotation offset starts at this distance
from the current next text offset.

**Arguments**:

- `min` - minimum gap size (default: 0)
- `max` - maximum gap size (default: 0)
  

**Returns**:

  parser that tries to match only if the next annotation is within the gap range

<a name="gatenlp.pam.pampac._AnnBase.findgap"></a>
#### findgap

```python
 | findgap(min=0, max=0)
```

Return a parser which matches at the next location where an annotation satisfies the gap constraint
with respect to the current text location.

**Arguments**:

- `min` - minimum gap size (default 0)
- `max` - maximum gap size (default 0)
  

**Returns**:

  parser that tries to match at the next annotation found within the gap range

<a name="gatenlp.pam.pampac.AnnAt"></a>
## AnnAt Objects

```python
class AnnAt(_AnnBase)
```

Parser for matching the first or all annotations at the offset for the next annotation in the list.

<a name="gatenlp.pam.pampac.AnnAt.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(type=None, features=None, features_eq=None, text=None, matchtype="first", name=None, useoffset=True)
```

Create an AnnAt parser.

**Arguments**:

- `type` - the type to match, can be None, a string, a regular expression or a callable
- `features` - the features that must be matched, a dictionary as the FeatureMatcher arguments
- `features_eq` - the features that must be matched and no other features may exist, a dictionary as
  the FeatureEqMatcher arguments.
- `text` - the covered document text to match
- `matchtype` - which matches to return in a success, one of "all", "first" (default), "longest", "shortest"
- `name` - the name of the match. If specified, a dictionary describing the match is added to the result.
- `useoffset` - if True, tries to match at the current text offset, not the start offset of the
  next annotation to match.

<a name="gatenlp.pam.pampac.Ann"></a>
## Ann Objects

```python
class Ann(_AnnBase)
```

Parser for matching the next annotation in the annotation list.

<a name="gatenlp.pam.pampac.Ann.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(type=None, features=None, features_eq=None, text=None, name=None, useoffset=True)
```

**Arguments**:

- `type` - (default: None): type to match, string, regexp or predicate function
- `features` - (default: None): features to match, dictionary where each value is value, regexp or predicate function
  Annotation can contain additional features.
- `features_eq` - (default: None): features to match, annotation must not contain additional features
- `text` - (default: None): document text to match, string or regexp
- `name` - (default: None): if set to a non-empty string, saves the data and assigns that name to the data
- `useoffset` - if True, and a location is give where the next annotation starts before the text offset, skips
  forward in the annotation list until an annotation is found at or after that offset.
  If no such annotation found, fails. If False, always uses the next annotation in the list, no matter
  the offset.

<a name="gatenlp.pam.pampac.Find"></a>
## Find Objects

```python
class Find(PampacParser)
```

A parser that tries another parser at successive offsets or annotations until it matches
the end of the document / parsing range is reached.

<a name="gatenlp.pam.pampac.Find.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(parser, by_anns=True)
```

**Arguments**:

- `parser` - the parser to use for finding the match
- `by_anns` - if True, tries at each annotation index and the corresponding text offset, otherwise tries
  at each text offset and the corresponding ann index.

<a name="gatenlp.pam.pampac.Text"></a>
## Text Objects

```python
class Text(PampacParser)
```

A parser that matches some text or regular expression.

<a name="gatenlp.pam.pampac.Text.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(text, name=None, matchcase=True)
```

**Arguments**:

- `text` - either text or a compiled regular expression
- `name` - the name of the matcher, if None, no data is stored
- `matchcase` - if text is actual text, whether the match should be case sensitive or not

<a name="gatenlp.pam.pampac.Or"></a>
## Or Objects

```python
class Or(PampacParser)
```

Create a parser that accepts the first seccessful one of all the parsers specified.

<a name="gatenlp.pam.pampac.Or.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(*parsers, *, matchtype="all")
```

Creates a parser that tries each of the given parsers in order and uses the first
one that finds a successful match.

**Arguments**:

- `*parsers` - two or more parsers to each try in sequence
- `matchtype` - which of the results from the successful parser to return.

<a name="gatenlp.pam.pampac.And"></a>
## And Objects

```python
class And(PampacParser)
```

Return a parser that is successful if all the parsers match at some location, and
fails otherwise. Success always contains all results from all parsers.

<a name="gatenlp.pam.pampac.And.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(*parsers)
```

Create an And parser.

**Arguments**:

- `*parsers` - a list of two or more parsers.

<a name="gatenlp.pam.pampac.All"></a>
## All Objects

```python
class All(PampacParser)
```

Return a parser that succeeds if one or more parsers succeed at some location.
If success, all results from all succeeding parsers are included.

<a name="gatenlp.pam.pampac.All.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(*parsers)
```

Create an All parser.

**Arguments**:

- `*parsers` - list of two ore more parsers.

<a name="gatenlp.pam.pampac.Seq"></a>
## Seq Objects

```python
class Seq(PampacParser)
```

A parser that represents a sequence of matching parsers. Each result of this parser combines
all the data from the sequence element parsers. For matchtype all and select all, all paths
through all the possible ways to match the sequence get combined into separate results of
a successful parse.

<a name="gatenlp.pam.pampac.Seq.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(*parsers, *, matchtype="first", select="first", name=None)
```

**Arguments**:

- `*parsers` - two or more parsers
- `matchtype` - (default "first") one of "first", "longest", "shortest", "all": which match to return.
  Note that even if a matchtype for a single match is specified, the parser may still need to
  generate an exponential number of combinations for all the results to select from.
- `select` - (default "first") one of "first", "longest", "shortest", "all": which match to choose from each
  of the parsers. Only if "all" is used will more than one result be generated.
- `name` - if not None, a separate data element is added to the result with that name and
  a span that represents the span of the result.

<a name="gatenlp.pam.pampac.N"></a>
## N Objects

```python
class N(PampacParser)
```

A parser that represents a sequence of k to l matching parsers.

If no until parser is given, the parser matches greedily as many times as possible.
The until parser can be used to make the matching stop as soon as the until parser succeeds.

<a name="gatenlp.pam.pampac.N.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(parser, min=1, max=1, matchtype="first", select="first", until=None, name=None)
```

Return a parser that matches min to max matches of parser in sequence. If until is specified, that
parser is tried to match before each iteration and as soon as it matched, the parser succeeds.
If after ming to max matches of the parser, until does not match, the parser fails.

**Arguments**:

- `parser` - the parser that should match min to max times
- `min` - minimum number of times to match for a success
- `max` - maximum number of times to match for a success
- `matchtype` - which results to include in a successful match, one of first, longest, shortest, all
- `until` - parser that terminates the repetition
- `name` - if not None, adds an additional data element to the result which contains the
  and span of the whole sequence.

<a name="gatenlp.pam.pampac.Rule"></a>
## Rule Objects

```python
class Rule(PampacParser)
```

A matching rule: this defines the parser and some action (a function) to carry out if the rule matches
as it is tried as one of many rules with a Pampac instance. Depending on select setting for pampac
the action only fires under certain circumstances (e.g. the rule is the first that matches at a location).
Rule is thus different from pattern.call() or Call(pattern, func) as these always call the function if
there is a successful match.

<a name="gatenlp.pam.pampac.Rule.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(parser, action, priority=0)
```

Create a Rule.

**Arguments**:

- `parser` - the parser to match for the rule
- `action` - the action to perform, or a function to call
- `priority` - the priority of the rule

<a name="gatenlp.pam.pampac.Rule.set_priority"></a>
#### set\_priority

```python
 | set_priority(val)
```

Different way of setting the priority.

<a name="gatenlp.pam.pampac.Rule.parse"></a>
#### parse

```python
 | parse(location, context)
```

Return the parse result. This does NOT automatically invoke the action if the parse result is a success.
The invoking Pampac instance decides, based on its setting, for which matching rules the action is
actually carried out.

**Returns**:

  Success or failure of the parser

<a name="gatenlp.pam.pampac.Pampac"></a>
## Pampac Objects

```python
class Pampac()
```

A class for applying a sequence of rules to a document.

<a name="gatenlp.pam.pampac.Pampac.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(*rules, *, skip="longest", select="first")
```

Initialize Pampac.

**Arguments**:

- `*rules` - one or more rules
- `skip` - how proceed after something has been matched at a position. One of: "longest" to proceed
  at the next text offset after the end of the longest match. "next" to use a location with the highest
  text and annotation index over all matches. "one" to increment the text offset by one and adjust
  the annotation index to point to the next annotation at or after the new text offset.
- `"once"` - do not advance after the first location where a rule matches. NOTE: if skipping depends on
  on the match(es), only those matches for which a rule fires are considered.
- `select` - which of those rules that match to actually apply, i.e. call the action part of the rule.
  One of: "first": try all rules in sequence and call only the first one that matches. "highest": try
  all rules and only call the rules which has the highest priority, if there is more than one, the first
  of those.

<a name="gatenlp.pam.pampac.Pampac.set_skip"></a>
#### set\_skip

```python
 | set_skip(val)
```

Different way to set the skip parameter.

<a name="gatenlp.pam.pampac.Pampac.set_select"></a>
#### set\_select

```python
 | set_select(val)
```

Different way to set the select parameter.

<a name="gatenlp.pam.pampac.Pampac.run"></a>
#### run

```python
 | run(doc, annotations, outset=None, start=None, end=None, debug=False)
```

Run the rules from location start to location end (default: full document), using the annotation set or list.

**Arguments**:

- `doc` - the document to run on
- `annotations` - the annotation set or iterable to use
- `outset` - the output annotation set.
- `start` - the text offset where to start matching
- `end` - the text offset where to end matching
  

**Returns**:

  a list of tuples (offset, actionreturnvals) for each location where one or more matches occurred

<a name="gatenlp.pam.pampac.AddAnn"></a>
## AddAnn Objects

```python
class AddAnn()
```

Action for adding an annotation.

<a name="gatenlp.pam.pampac.AddAnn.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name=None, ann=None, anntype=None, features=None, span=None, resultidx=0, dataidx=0, silent_fail=False)
```

Create an action for adding a new annotation to the outset.

**Arguments**:

- `name` - the name of the match to use for getting the annotation span
- `ann` - either an Annotation which will be (deep) copied to create the new annotation, or
  a GetAnn helper for copying the annoation the helper returns. If this is specified the
  other parameters for creating a new annotation are ignored.
- `anntype` - the type of a new annotation to create
- `features` - the features of a new annotation to create. This can be a GetFeatures helper for copying
  the features from another annotation in the results
- `span` - the span of the annotation, this can be a GetSpan helper for copying the span from another
  annotation in the results
- `resultidx` - the index of the result to use if more than one result is in the Success
- `dataidx` - the index of the data item to use if more than one item matches the given name
- `silent_fail` - if True and the annotation can not be created for some reason, just do silently nothing,
  otherwise raises an Exception.

<a name="gatenlp.pam.pampac.UpdateAnnFeatures"></a>
## UpdateAnnFeatures Objects

```python
class UpdateAnnFeatures()
```

Action for updating the features of an annotation.

<a name="gatenlp.pam.pampac.UpdateAnnFeatures.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name, ann=None, features=None, replace=False, resultidx=0, dataidx=0, silent_fail=False)
```

Create an UpdateAnnFeatures action.

**Arguments**:

- `name` - the name of the match to use for getting the annotation span
- `ann` - if specified use the features from this annotation. This can be either a literal annotation
  or a GetAnn helper to access another annotation from the result.
- `features` - the features to use for updating, either literal  features or a GetFeatures helper.
- `replace` - if True, replace the existing features with the new ones, otherwise update the existing features.
- `resultidx` - the index of the result to use, if there is more than one
- `dataidx` - the index of a matching data element to use, if more than one matches the given name
- `silent_fail` - if True, do not raise an exception if the features cannot be updated

<a name="gatenlp.pam.pampac.GetAnn"></a>
## GetAnn Objects

```python
class GetAnn()
```

Helper to access an annoation from a match with the given name.

<a name="gatenlp.pam.pampac.GetAnn.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name, resultidx=0, dataidx=0, silent_fail=False)
```

Create a GetAnn helper.

**Arguments**:

- `name` - the name of the match to use.
- `resultidx` - the index of the result to use if there is more than one.
- `dataidx` - the index of the data element with the given name to use if there is more than one
- `silent_fail` - if True, do not raise an exception if the annotation cannot be found, instead return
  None.

<a name="gatenlp.pam.pampac.GetFeatures"></a>
## GetFeatures Objects

```python
class GetFeatures()
```

Helper to access the features of an annotation in a match with the given name.

<a name="gatenlp.pam.pampac.GetFeatures.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name, resultidx=0, dataidx=0, silent_fail=False)
```

Create a GetFeatures helper.

**Arguments**:

- `name` - the name of the match to use.
- `resultidx` - the index of the result to use if there is more than one.
- `dataidx` - the index of the data element with the given name to use if there is more than one
- `silent_fail` - if True, do not raise an exception if the annotation cannot be found, instead return
  None

<a name="gatenlp.pam.pampac.GetType"></a>
## GetType Objects

```python
class GetType()
```

Helper to access the type of an annotation in a match with the given name.

<a name="gatenlp.pam.pampac.GetType.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name, resultidx=0, dataidx=0, silent_fail=False)
```

Create a GetType helper.

**Arguments**:

- `name` - the name of the match to use.
- `resultidx` - the index of the result to use if there is more than one.
- `dataidx` - the index of the data element with the given name to use if there is more than one
- `silent_fail` - if True, do not raise an exception if the annotation cannot be found, instead return
  None

<a name="gatenlp.pam.pampac.GetStart"></a>
## GetStart Objects

```python
class GetStart()
```

Helper to access the start offset of the annotation in a match with the given name.

<a name="gatenlp.pam.pampac.GetStart.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name, resultidx=0, dataidx=0, silent_fail=False)
```

Create a GetStart helper.

**Arguments**:

- `name` - the name of the match to use.
- `resultidx` - the index of the result to use if there is more than one.
- `dataidx` - the index of the data element with the given name to use if there is more than one
- `silent_fail` - if True, do not raise an exception if the annotation cannot be found, instead return
  None

<a name="gatenlp.pam.pampac.GetEnd"></a>
## GetEnd Objects

```python
class GetEnd()
```

Helper to access the end offset of the annotation in a match with the given name.

<a name="gatenlp.pam.pampac.GetEnd.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name, resultidx=0, dataidx=0, silent_fail=False)
```

Create a GetEnd helper.

**Arguments**:

- `name` - the name of the match to use.
- `resultidx` - the index of the result to use if there is more than one.
- `dataidx` - the index of the data element with the given name to use if there is more than one
- `silent_fail` - if True, do not raise an exception if the annotation cannot be found, instead return
  None

<a name="gatenlp.pam.pampac.GetFeature"></a>
## GetFeature Objects

```python
class GetFeature()
```

Helper to access the features of the annotation in a match with the given name.

<a name="gatenlp.pam.pampac.GetFeature.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name, featurename, resultidx=0, dataidx=0, silent_fail=False)
```

Create a GetFeatures helper.

**Arguments**:

- `name` - the name of the match to use.
- `resultidx` - the index of the result to use if there is more than one.
- `dataidx` - the index of the data element with the given name to use if there is more than one
- `silent_fail` - if True, do not raise an exception if the annotation cannot be found, instead return
  None

<a name="gatenlp.pam.pampac.GetText"></a>
## GetText Objects

```python
class GetText()
```

Helper to access the covered document text of the annotation in a match with the given name.

<a name="gatenlp.pam.pampac.GetText.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name, resultidx=0, dataidx=0, silent_fail=False)
```

Create a GetText helper.

**Arguments**:

- `name` - the name of the match to use.
- `resultidx` - the index of the result to use if there is more than one.
- `dataidx` - the index of the data element with the given name to use if there is more than one
- `silent_fail` - if True, do not raise an exception if the annotation cannot be found, instead return
  None

<a name="gatenlp.pam.pampac.GetRegexGroup"></a>
## GetRegexGroup Objects

```python
class GetRegexGroup()
```

Helper to access the given regular expression matching group in a match with the given name.

<a name="gatenlp.pam.pampac.GetRegexGroup.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name, group=0, resultidx=0, dataidx=0, silent_fail=False)
```

Create a GetText helper.

**Arguments**:

- `name` - the name of the match to use.
- `resultidx` - the index of the result to use if there is more than one.
- `dataidx` - the index of the data element with the given name to use if there is more than one
- `silent_fail` - if True, do not raise an exception if the annotation cannot be found, instead return
  None

