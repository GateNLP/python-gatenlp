#!/usr/bin/env python
"""
Module for PAMPAC (Pattern Matching wit PArser Combinators) which allows to create parsers that can match
patterns in annotations and text and carry out actions if a match occurs.

NOTE: this implementation has been inspired by https://github.com/google/compynator
"""
import functools
import collections
from collections.abc import Iterable, Sized
from abc import ABC, abstractmethod
from .matcher import FeatureMatcher, FeatureEqMatcher, AnnMatcher, CLASS_REGEX_PATTERN, CLASS_RE_PATTERN

class ParseLocation:
    """
    A ParseLocation represents the next location in the text and annotation list where a parser will try to
    match, i.e. the location after everything that has been consumed by the parser so far.

    The text offset equal to the length of the text represent the EndOfText condition and the annotation index
    equal to the length of the annotation list represents the EndOfAnns condition.
    """
    def __init__(self, text_location=0, ann_location=0):
        self.text_location = text_location
        self.ann_location = ann_location

    def __str__(self):
        return f"Location({self.text_location},{self.ann_location})"

    def __repr__(self):
        return f"Location({self.text_location},{self.ann_location})"

class Result:
    def __init__(self, data=None, location=None, context=None):
        if data is not None:
            if isinstance(data, dict):
                self.data = [data]
            elif isinstance(data, Iterable):
                self.data = list(data)
            else:
                self.data = [data]
        else:
            self.data = []
        self.location = location
        self.context = context

    def data4name(self, name):
        return [d for d in self.data if d.name == name]

    def __str__(self):
        return f"Result(loc={self.location},ndata={len(self.data)})"

    def __repr__(self):
        return f"Result(loc={self.location},data={self.data})"

class Failure:
    """
    Represents a parse failure.
    """
    def __init__(self, message=None, parser=None, location=None, causes=None, context=None, ):
        self.context = context
        self._parser = parser
        if not message:
            message = "Parser Error"
        self.message = message
        if location:
            self._cur_text = location.text_location
            self._cur_ann = location.ann_location
        else:
            self._cur_text = "?"
            self._cur_ann = "?"
        if isinstance(causes, Failure):
            self._causes = [causes]
        else:
            self._causes = causes

    def issuccess(self):
        return False

    def _get_causes(self):
        for cause in self._causes:
            if not cause._causes:
                # The root cause since there's no further failures.
                yield cause
            else:
                yield from cause._get_causes()

    def describe(self, indent=4, level=0):
        lead = ' ' * indent * level
        desc = (
            f'{lead}{self._parser} at {self._cur_text}/{self._cur_ann}: '
            f'{self.message}'
        )
        tail = ''
        if self._causes:
            tail = (
                    f'\n{lead}Caused by:\n' +
                    '\n'.join(x.describe(indent, level + 1)
                              for x in self._get_causes())
            )
        return desc + tail

    def __str__(self):
        return self.describe()

    def __repr__(self):
        return (
            f'{self.__class__.__name__}({self.message!r}, '
            f'{self._cur_text!r}/{self._cur_ann}, {self._causes!r})'
        )

class Success(Iterable, Sized):
    """
    Represents a parse success as a possibly empty list of result elements.
    """
    def __init__(self, results=None):
        if results is None:
            self._results = []
        elif isinstance(results, Iterable):
            self._results = list(results)
        else:
            self._results = [results]

    def issuccess(self):
        return True

    def add(self, result, ifnew=False):
        # TODO: not sure if the ifnew parameter and treatment makes sense: do we ever not want
        # to add a result if it is already there (meaning, the same match and the same remaining text/anns).
        if isinstance(result, Iterable):
            for re in result:
                self.add(re, ifnew=ifnew)
        else:
            if ifnew:
                if result not in self._results:
                    self._results.append(result)
            else:
                self._results.append(result)
        return self

    def __iter__(self):
        return iter(self._results)

    def __len__(self):
        return len(self._results)

    def __eq__(self, other):
        if not isinstance(other, Success):
            return False
        return self._results == other._results

    def __str__(self):
        return str(self._results)

    def __getitem__(self, item):
        return self._results[item]

class Context:
    """
    Context contains data and refers to data for carrying out the parse. Only the memoize data changes
    in the context, all other fields are treated as immutable during a parse.
    """
    def __init__(self, doc, anns, start=None, end=None, memoize=False, max_recusion=None):
        """
        start is the offset in the original document to where we start parsing, text is the full
        document text, start is the first offset from where we start parsing, end is the offset
        which we should not parse anymore (one after the actual last offset to include).
        """
        self._memotable = {}
        self.max_recursion = max_recusion
        self.doc = doc
        # make sure the start and end offsets are plausible or set the default to start/end of document
        if start is None:
            self.start = 0
        else:
            if start >= len(doc.text) or start < 0:
                raise Exception("Invalid start offset: {start}, document length is {len(doc.text}")
            self.start = start
        if end is None:
            self.end = len(doc.text)   # offset after the last text character!
        else:
            if end <= start or end > len(doc.text):
                raise Exception("Invalid end offset: {end}, start is {self.start}")
            self.end = end
        # make sure all the anns are within the given offset range
        anns = [a for a in anns if a.start >= self.start and a.end <= self.end]
        self.anns = anns
        self.memoize = memoize

    def get_ann(self, location):
        """
        Return the ann at the given location, or None if there is none.

        Returns:
            annotation or None
        """
        if location.ann_location >= len(self.anns):
            return None
        return self.anns[location.ann_location]

    def nextidx4offset(self, location, offset, next_ann=False):
        """
        Return the index of the next annotation that starts at or after the given text offset.
        If no such annotation exists the end of annotations index (equal to length of annotations) is returned.

        Args:
            location: current location, the annotation is searched from the annotation index following the one in the
               current location
            offset: offset to look for
            next_ann: if True, always finds the NEXT annotation after the one pointed at with the current location.
               If false keeps the current one if it is still the next one.

        Returns:
            annotation index
        """
        idx = location.ann_location
        if next_ann:
            idx += 1
        while True:
            if idx >= len(self.anns):
                return len(self.anns)
            ann = self.anns[idx]
            if ann.start >= offset:
                return idx
            idx += 1

    def inc_location(self, location, by_offset=None, by_index=None):
        """
        Return a new location which represents the given location incremented by either the given number of index
        count (usually 1), or by the given offset length. Only one of the by parameters should be specified.

        If the update occurs by offset, then the annotation index is updated to that of the next index with
        a start offset equal or larger than the updated text offset.  This may be the end of annotations index.
        If the text offset hits the end of text offset, the annotation index is set to the end of annotations index.

        If the update occurs by index, then the text offset is updated to the offset corresponding to the end offset
        of the annotation, if there is one.


        Args:
            location:
            by_offset: the number of text characters to increment the text offset by
            by_index:  the number of annotations to increment the index by

        Returns:
            new location
        """
        newloc = ParseLocation(text_location=location.text_location, ann_location=location.ann_location)
        if by_index is not None:
            # get the annotation before the one we want to point at next, so we get the end offset of the
            # last annotation consumed
            newloc.ann_location += by_index-1
            ann = self.get_ann(location)
            # if we already are at the end of the annotations, just leave everything as it is
            if not ann:
                return location
            newloc.text_location = ann.end
            # this is now the index of the next ann or the end of anns index
            newloc.ann_location += 1
        else:
            # update by text offset
            if newloc.text_location + by_offset >= self.end:
                # if we reach the end of the text, update the annotation index to end of annotations as well
                newloc.text_location = self.end
                newloc.ann_location = len(self.anns)
            else:
                # otherwise try to find the next matching annotation
                print(f"DEBUG: before incrementing by offset: {newloc}")
                newloc.text_location += by_offset
                newloc.ann_location = self.nextidx4offset(location, newloc.text_location)
                print(f"DEBUG: after incrementing by offset: {newloc}")
                # if we got end of annotations index, we do NOT update the text to end of text!
                # we could still want to match something in the text after the last annotation.
        return newloc

    def at_endoftext(self, location):
        """
        Returns true if the location represents the end of text location

        Args:
            location: location

        Returns:
            True if we are at end of text
        """
        return location.text_location >= self.end

    def at_endofanns(self, location):
        """
        Returns true if the location represents the end of anns location

        Args:
            location: location

        Returns:
            True if we are at end of anns
        """
        return location.ann_location >= len(self.anns)


class Parser:
    """
    An actual parser, something that takes a context and returns a result.
    This can be used to decorate a function that should be used as the parser,
    or for subclassing specific parsers. When subclassing, the parse(location, context)
    method must be overriden
    """
    def __init__(self, parser_function):
        self.name = None
        self._parser_function = parser_function
        self.name = parser_function.__name__
        functools.update_wrapper(self, parser_function)

    def parse(self, location, context):
        return self._parser_function(location, context)

    __call__ = parse

    def call(self, func, onfailure=None):
        """
        Returns a parser that is equivalent to this parser, but also calls the given function if there is success.
        Args:
            func:

        Returns:

        """
        return Rule(self, func, onfailure=onfailure)


class Rule:
    def __init__(self, parser, func, onfailure=None, priority=100):
        self.parser = parser
        self.func = func
        self.onfailure = onfailure
        self.priority = priority

    def parse(self, location, context):
        ret = self.parser.parse(location, context)
        if ret.issuccess():
            self.func(ret, name=self.parser.name, parser=self.parser.__class__.__name__)
        else:
            if self.onfailure:
                self.onfailure(ret, name=self.parser.name, parser=self.parser.__class__.__name__)
        return ret


class AnnAt(Parser):
    """
    Parser for matching the first or all annotations at the offset for the next annotation in the list.
    """
    def __init__(self, type=None, features=None, features_eq=None, text=None, match_all=False, name=None):
        self.type = type
        self.features = features
        self.features_eq = features_eq
        self.text = text
        self.name = name
        self._matcher = AnnMatcher(type=type, features=features, features_eq=features_eq, text=text)
        self.match_all = match_all

    def parse(self, location, context):
        next_ann = context.get_ann(location)
        if not next_ann:
            return Failure(
                context=context,
                location=location,
                parser=self,
                message="No annotation left")
        datas = []
        start = next_ann.start
        matched = False
        while True:
            print(f"DEBUG: Trying matcher at {location}, got ann {next_ann}")
            if self._matcher(next_ann):
                matched = True
                matchlocation = ParseLocation(text_location=start, ann_location=location.ann_location)
                print(f"DEBUG: Matchlocation is {location}")
                data = dict(location=matchlocation, ann=next_ann, name=self.name, parser=self.__class__.__name__)
                if self.name:
                    datas.append(data)
                # update location
                location = context.inc_location(location, by_index=1)
                print(f"DEBUG: Incremented location {location}")
                if not self.match_all:
                    return Success(Result(data=datas, location=location))
                next_ann = context.get_ann(location)
                print(f"DEBUG: got new next ann: {next_ann}")
                if not next_ann or next_ann.start != start:
                    break
            else:
                location = context.inc_location(location, by_index=1)
                next_ann = context.get_ann(location)
                print(f"DEBUG: got new next ann for loc {location} in else: {next_ann}")
                if not next_ann or next_ann.start != start:
                    break
        if not matched:
            print("NOT MATCHED")
            return Failure(
                context=context,
                parser=self,
                location=location,
                message="No matching annotation")
        else:
            return Success(Result(data=datas, location=location))


class Ann(Parser):
    """
    Parser for matching the next annotation in the annotation list.
    """
    def __init__(self, type=None, features=None, features_eq=None, text=None, name=None):
        self.type = type
        self.features = features
        self.features_eq = features_eq
        self.text = text
        self.name = name
        self._matcher = AnnMatcher(type=type, features=features, features_eq=features_eq, text=text)

    def parse(self, location, context):
        """
        Try to match the given annotation at the current context location. If we succeed,

        Args:
            location: the location of where to parse next
            context: parser context

        Returns:
            Success or Failure
        """
        next_ann = context.get_ann(location)
        if not next_ann:
            return Failure(
                context=context,
                parser=self,
                location=location,
                message="No annotation left")
        # try to match it
        if self._matcher(next_ann, doc=context.doc):
            newlocation = context.inc_location(location, by_index=1)
            if self.name:
                data = dict(location=location, ann=next_ann, name=self.name, parser=self.__class__.__name__)
            else:
                data = None
            return Success(
                Result(context=context, data=data, location=newlocation)
            )
        else:
            return Failure(location=location, context=context, parser=self)

class Find:
    """
    A parser that tries another parser until it matches.
    """
    def __init__(self, parser, by_anns=True):
        """

        Args:
            parser: the parser to use for finding the match
            by_anns: if True, tries at each annotation index and the corresponding text offset, otherwise tries
               at each text offset and the corresponding ann index.
        """
        self.parser = parser
        self.by_anns = by_anns

    def parse(self, location, context):
        while True:
            print(f"DEBUG: trying to parse at {location}, lendoc={len(context.doc.text)}")
            ret = self.parser.parse(location, context)
            if ret.issuccess():
                return ret
            else:
                if self.by_anns:
                    location = context.inc_location(location, by_index=1)
                    if context.at_endofanns(location):
                        return Failure(context=context, message="Not found via anns", location=location)
                else:
                    print(f"DEBUG: before increment: {location}, end={context.end}")
                    location = context.inc_location(location, by_offset=1)
                    print(f"DEBUG: after increment: {location}, end={context.end}")
                    if context.at_endoftext(location):
                        return Failure(context=context, message="Not found via text", location=location)



class Seq:
    """
    A parser that represents a sequence of matching parsers.
    """
    pass

class N:
    """
    A parser that represents a sequence of k to l matching parsers, greedy.
    """
    pass


class Text:
    """
    A parser that matches some text or regular expression
    """
    def __init__(self, text, name=None, matchcase=True):
        """

        Args:
            text: either text or a compiled regular expression
            name:  the name of the matcher, if None, no data is stored
            matchcase: if text is actual text, whether the match should be case sensitive or not
        """
        self.text = text
        if isinstance(self.text, str) and not matchcase:
            self.text = self.text.upper()
        self.name = name
        self.matchcase = matchcase

    def parse(self, location, context):
        txt = context.doc.text[location.text_location:]
        if isinstance(self.text, CLASS_RE_PATTERN) or isinstance(self.text, CLASS_REGEX_PATTERN):
            m = self.text.match(txt)
            if m:
                l = len(m.group())
                newlocation = context.inc_location(location, by_offset=l)
                if self.name:
                    data = dict(
                        location=location,
                        text=m.group(),
                        groups=m.groups(),
                        name=self.name,
                        parser=self.__class__.__name__
                    )
                else:
                    data = None
                return Success(
                    results=Result(
                        data=data,
                        location=newlocation
                    )
                )
            else:
                return Failure(context=context)
        else:
            if not self.matchcase:
                txt = txt.upper()
            if txt.startswith(self.text):
                if self.name:
                    data = dict(location=location, text=self.text, name=self.name, parser=self.__class__.__name__)
                else:
                    data = None
                newlocation = context.inc_location(location, by_offset=len(self.text))
                return Success(results=Result(data=data, location=newlocation))
            else:
                return Failure(context=context)
