"""
Module for PAMPAC (Pattern Matching wit PArser Combinators) which allows to create parsers that can match
patterns in annotations and text and carry out actions if a match occurs.

NOTE: this implementation has been inspired by https://github.com/google/compynator
"""
import functools
from copy import deepcopy
from collections.abc import Iterable, Sized
from .matcher import AnnMatcher, CLASS_REGEX_PATTERN, CLASS_RE_PATTERN
from gatenlp.utils import support_annotation_or_set
from gatenlp import AnnotationSet, Annotation
from gatenlp.utils import init_logger
from gatenlp import Span

__pdoc__ = {
    "PampacParser.__or__": True,
    "PampacParser.__xor__": True,
    "PampacParser.__rshift__": True,
    "PampacParser.__and__": True,
    "PampacParser.__mul__": True,
    "_AnnBase": True,
}


# NOTES: Backreferences: to hard to implement this in a flexible way, simply use Filter on the final result

# TODO: check that Context.end is respected with all individual parsers: we should not match beyond that offset!

# TODO: figure out which parser parameters could be implemented as parser modifiers instead/in addition???

# TODO: implement Gazetteer(gaz, matchtype=None) parser? Or TokenGazetteer(gaz, ...)
# TODO: implement Forward() / fwd.set(fwd | Ann("X"))
# TODO: implement support for literal Text/Regexp: Seq(Ann("Token"), "text", regexp) and Ann >> "text" and "text" >> Ann()
#   and Ann() | text etc.
# !!TODO: options for skip:
# !!TODO: * overlapping=True/False: sequence element can overlap with previous match
# !!TODO: * skip=True/False: skip forward in annotation list until we find annotation that fits
# !!TODO: * mingap=n, maxgap=n: gap between annotation must be in this range
# !!TODO: so A.followedby(B) is equal to Seq(A,B, mingap=0, maxgap=0, skip=False/True)
# mindist, maxdist: from start to start (mingap/maxgap; from end to start).
# !!TODO: implement memoize: save recursive result and check max recursion, modifier: parser.memoize(maxdepth=5)
#   for the wrapped parsers, before each call to the wrapped parser, we first check if the result is already in
#   the memotable and return it. If not, calculate recursion depth and Fail if too deep, otherwise call wrapped
#   parser and memoize (store Success or Failure)


class Location:
    """
    A ParseLocation represents the next location in the text and annotation list where a parser will try to
    match, i.e. the location after everything that has been consumed by the parser so far.

    The text offset equal to the length of the text represent the EndOfText condition and the annotation index
    equal to the length of the annotation list represents the EndOfAnns condition.
    """

    def __init__(self, text_location=0, ann_location=0):
        """
        Create a parser location.

        Args:
            text_location: the next text offset from which on to parse.
            ann_location:  the next annotation index from which on to parse.
        """
        self.text_location = text_location
        self.ann_location = ann_location

    def __str__(self):
        return f"Location({self.text_location},{self.ann_location})"

    def __repr__(self):
        return f"Location({self.text_location},{self.ann_location})"

    def __eq__(self, other):
        if not isinstance(other, Location):
            return False
        return (
            self.text_location == other.text_location
            and self.ann_location == other.ann_location
        )


class Result:
    """
    Represents an individual parser result. A successful parse can have any number of parser results which
    are alternate ways of how the parser can match the document.
    """

    def __init__(self, data=None, location=None, span=None):
        """
        Create a parser result.

        Args:
            data: the data associated with the result, this can be a single item or a list of items.
                Each item must be either a dictionary that describes an individual match or None.
            location: the location where the result was matched, i.e. the location *before* matching was done.
            span: the span representing the start and end text offset for the match
        """
        assert location is not None
        assert span is not None
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
        self.span = span

    def data4name(self, name):
        """
        Return a list of data dictionaries with the given name.
        """
        return [d for d in self.data if d.get("name") == name]

    def __str__(self):
        return f"Result(loc={self.location},span=({self.span.start},{self.span.end}),ndata={len(self.data)})"

    def __repr__(self):
        return f"Result(loc={self.location},span=({self.span.start},{self.span.end}),data={self.data})"


class Failure:
    """
    Represents a parse failure.
    """

    def __init__(
        self,
        message=None,
        parser=None,
        location=None,
        causes=None,
        context=None,
    ):
        """
        Create a Failure instance.

        Args:
            message: the message to describe the parse failure.
            parser (str): the class name of the parser
            location: the location at which the parser failed.
            causes:  another failure instance or a list of other failure instances which
                can be used to describe the failure of nested parsers in more detail
            context: the context at the point of failure. This is stored as a reference so
                the context should not get modified after the failure is constructed.
        """
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
        """
        Method for success and failure results which indicates if we have a success or failure.

        Returns:
            False

        """
        return False

    def _get_causes(self):
        for cause in self._causes:
            if not cause._causes:
                # The root cause since there's no further failures.
                yield cause
            else:
                yield from cause._get_causes()

    def describe(self, indent=4, level=0):
        """
        Return a string with information about the failure.

        Args:
            indent: number of characters to indent for each recursive failure.
            level: recursive level of failure

        Returns:
            String with information about the failure
        """
        lead = " " * indent * level
        desc = (
            f"{lead}{self._parser} at {self._cur_text}/{self._cur_ann}: "
            f"{self.message}"
        )
        tail = ""
        if self._causes:
            tail = f"\n{lead}Caused by:\n" + "\n".join(
                x.describe(indent, level + 1) for x in self._get_causes()
            )
        return desc + tail

    def __str__(self):
        return self.describe()

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.message!r}, "
            f"{self._cur_text!r}/{self._cur_ann}, {self._causes!r})"
        )


class Success(Iterable, Sized):
    """
    Represents a parse success as a (possibly empty) list of result elements.

    Each success is a list of result elements, and each result element contains a list
    of matching data. A result represents a match at the top/outermost level of a parser.
    A parser that is made of sub parsers and sub-sub-parsers returns one or more matches
    over all the different ways how those sub-parsers can match at a specific location,
    and each result contains a result element for all the named sub- and sub-sub-parsers
    the main parser is made of.
    """

    def __init__(self, results, context):
        """
        Create a Success instance.

        Args:
            results: a result or a list of results which may be empty
            context: the context used when parsing that result. A reference to the context is stored
               so the context may change after the result has been produced if it is used for more
               parsing.
        """
        if results is None:
            self._results = []
        elif isinstance(results, Iterable):
            self._results = list(results)
        else:
            self._results = [results]
        self.context = context

    def issuccess(self):
        """
        Method for success and failure results which indicates if we have a success or failure.

        Returns:
            True
        """
        return True

    # TODO: the following method may not be needed! Consider removing!
    # def add(self, result, ifnew=False):
    #     """
    #     Add a result.
    #
    #     Args:
    #         result:
    #         ifnew:
    #
    #     Returns:
    #
    #     """
    #     # TODO: not sure if the ifnew parameter and treatment makes sense: do we ever not want
    #     # to add a result if it is already there (meaning, the same match and the same remaining text/anns).
    #     if isinstance(result, Iterable):
    #         for re in result:
    #             self.add(re, ifnew=ifnew)
    #     else:
    #         if ifnew:
    #             if result not in self._results:
    #                 self._results.append(result)
    #         else:
    #             self._results.append(result)
    #     return self

    def pprint(self, file=None):
        """
        Pretty print the success instance to the file or stdout if no file is specified.

        Args:
            file: open file handle for use with print.
        """
        for idx, res in enumerate(self._results):
            if file:
                print(f"Result {idx}, location={res.location}:", file=file)
            else:
                print(f"Result {idx}, location={res.location}:", file=file)
            for jdx, d in enumerate(res.data):
                if file:
                    print(f"  {jdx}: {d}", file)
                else:
                    print(f"  {jdx}: {d}", file)

    @staticmethod
    def select_result(results, matchtype="first"):
        """
        Return the result described by parameter matchtype.

        If "all" returns the whole list of matches.

        Args:
            results: list of results to select from
            matchtype: one of  "first", "shortest", "longest", "all".
                If there is more than one longest or shortest
                result, the first one of those in the list is returned.

        Returns:
            the filtered result or all results
        """
        if matchtype is None:
            matchtype = "first"
        if matchtype == "all":
            return results
        elif matchtype == "first":
            return results[0]
        elif matchtype == "longest":
            result = results[0]
            loc = result.location
            for res in results:
                if res.location.text_location > loc.text_location:
                    loc = res.location
                    result = res
            return result
        elif matchtype == "shortest":
            result = results[0]
            loc = result.location
            for res in results:
                if res.location.text_location < loc.text_location:
                    loc = res.location
                    result = res
            return result
        else:
            raise Exception(f"Not a valid value for matchtype: {matchtype}")

    def result(self, matchtype="first"):
        """
        Return the result described by parameter matchtype. If "all" returns the whole list of matches.

        Args:
            matchtype: one of  "first", "shortest", "longest", "all".
                If there is more than one longest or shortest
                result, the first one of those in the list is returned.

        Returns:
            the filtered result or all results
        """
        return Success.select_result(self._results, matchtype)

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
    Context contains data and refers to data for carrying out the parse.

    A context contains a reference to the document being parsed, the list of annotations to use,
    the start and end text offsets the parsing should be restricted to, the output annotation set
    to use, the maximum recursion depth and a data structure for memoization.

    All these fields are immutable, i.e. the references stored do not usually change during parsing or
    when Pampac executes rules on a document. However, all the referenced data apart from start and
    end may change.

    """

    def __init__(
        self,
        doc,
        anns,
        start=None,
        end=None,
        outset=None,
        memoize=False,
        max_recusion=None,
    ):
        """
        Initialize a parse context.

        Args:
            doc: the document which should get parsed
            anns: an iterable of annotations to use for the parsing
            start: the starting text offset for the parse
            end: the ending text offset for the parse
            outset: an annotation set for where to add any new annotations in an action
            memoize: If memoization should be used (NOT YET IMPLEMENTED)
            max_recusion: the maximum recursion depth for recursive parse rules (NOT YET IMPLEMENTED)
        """
        self._memotable = {}
        self.max_recursion = max_recusion
        self.doc = doc
        self.outset = outset
        self._annset = (
            None  # cache for the annotations as a detached immutable set, if needed
        )
        # make sure the start and end offsets are plausible or set the default to start/end of document
        if start is None:
            self.start = 0
        else:
            if start >= len(doc.text) or start < 0:
                raise Exception(
                    "Invalid start offset: {start}, document length is {len(doc.text}"
                )
            self.start = start
        if end is None:
            self.end = len(doc.text)  # offset after the last text character!
        else:
            if end <= start or end > len(doc.text):
                raise Exception("Invalid end offset: {end}, start is {self.start}")
            self.end = end
        # make sure all the anns are within the given offset range
        anns = [a for a in anns if a.start >= self.start and a.end <= self.end]
        self.anns = anns
        self.memoize = memoize

    @property
    def annset(self):
        """
        Return the annotations as a set.

        Returns:
            annotations as a detached immutable AnnotationSet
        """
        if self._annset is None:
            self._annset = AnnotationSet.from_anns(self.anns)
        return self._annset

    def get_ann(self, location):
        """
        Return the ann at the given location, or None if there is none (mainly for the end-of-anns index).

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
        newloc = Location(
            text_location=location.text_location, ann_location=location.ann_location
        )
        if by_index is not None:
            # get the annotation before the one we want to point at next, so we get the end offset of the
            # last annotation consumed
            newloc.ann_location += by_index - 1
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
                newloc.text_location += by_offset
                newloc.ann_location = self.nextidx4offset(
                    location, newloc.text_location
                )
                # if we got end of annotations index, we do NOT update the text to end of text!
                # we could still want to match something in the text after the last annotation.
        return newloc

    def update_location_byoffset(self, location):
        """
        Update the passed location so that the annotation index is updated by the text offset: all annotations are
        skipped until the start offset of the annotation is at or past the text offset.

        Args:
            location: the location to update

        Returns:
            a new location with the annotation index updated
        """
        for i in range(location.ann_location, len(self.anns)):
            if self.anns[i].start >= location.text_location:
                return Location(location.text_location, i)
        return Location(location.text_location, len(self.anns))

    def update_location_byindex(self, location):
        """
        Update the passed location from the annotation index and make sure it points to the end of the current
        annotation or the end of the document.

        Args:
            location: the location to update

        Returns:
            a new location with the text offset updated
        """
        if location.ann_location == len(self.anns):
            return Location(len(self.doc.text), location.ann_location)
        else:
            return Location(
                location.text_location, self.anns[location.ann_location].end
            )

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


class PampacParser:
    """
    A Pampac parser, something that takes a context and returns a result.
    This can be used to decorate a function that should be used as the parser,
    or for subclassing specific parsers.

    When subclassing, the method `parse(location, context)`  must be overriden!

    All parsers are callables where the `__call__` method has the same signature as the
    `match` method. So `SomeParser(...)(doc, anns)` is the same as `SomeParser(...).match(doc, anns)`

    """

    def __init__(self, parser_function):
        """
        Create a parser from the given function.

        Args:
            parser_function: the function to wrap into a parser.
        """
        self.name = None
        self._parser_function = parser_function
        self.name = parser_function.__name__
        functools.update_wrapper(self, parser_function)

    def parse(self, location, context):
        """
        Invoking the parser function. This invokes the wrapped function for the root PampacParser
        class and should be overriden/implemented for PampacParser subclasses.

        Args:
            location: where to start parsing
            context: the parsing context

        Returns:
            Success or Failure
        """
        return self._parser_function(location, context)

    def match(self, doc, anns=None, start=None, end=None, location=None):
        """
        Runs the matcher/parser on the given document and the given annotations.

        Annotations may be empty in which case only matching on text makes sense.

        Args:
            doc: the document to run matching on.
            anns: (default: None) a set or Iterable of annotations. If this is a list or Iterable, the annotations
               will get matched in the order given. If it is a set the "natural" order of annotations used
               by the annotation set iterator will be used.
            start:  the minimum text offset of a range where to look for matches. No annotations that start before
               that offset are included.
            end: the maximum text offset of a range where to look for matches. No annotation that ends after that
               offset and not text that ends after that offset should get included in the result.

        Returns:
            Success or Failure
        """
        if anns is None:
            anns = []
        else:
            anns = list(anns)
        ctx = Context(doc, anns, start=start, end=end)
        if location is None:
            location = Location(ctx.start, 0)
        return self.parse(location, ctx)

    __call__ = match

    def call(self, func, onfailure=None):
        """
        Returns a parser that is equivalent to this parser, but also calls the given function if there is success.

        Args:
            func: the function to call on the success. Should take the success object and arbitrary kwargs.
                context and location are kwargs that get passed.
            onfailure: the function to call on failure. Should take the failure object and arbitrary kwargs.
                context and location are kwargs that get passed.

        Returns:

        """
        return Call(self, func, onfailure=onfailure)

    def __or__(self, other):
        """
        Binary Or via the `|` operator.

        This allows to write `Parser1(..) | Parser2(..)` instead of `Or(Parser1(..), Parser2(...))`

        Args:
            other: the other parser

        Returns:
            A parser that succeeds if either this or the other parser succeeds.
        """
        return Or(self, other)

    def __rshift__(self, other):
        """
        Binary Seq via the `>>` operator.

        This allows to write `Parser1(..) >> Parser2(..)` instead of `Seq(Parser1(..), Parser2(...))`

        Args:
            other: the other parser

        Returns:
            A parser that succeeds if this parser succeeds and then the other parser succeeds
            after it.
        """
        return Seq(self, other)

    def __and__(self, other):
        """
        Binary And via the `&` operator.

        This allows to write `Parser1(..) & Parser2(..)` instead of `And(Parser1(..), Parser2(...))`

        Args:
            other: the other parser

        Returns:
            A parser that succeeds if this parser and the other parser both succeed at the same location.
        """
        return And(self, other)

    def __xor__(self, other):
        """
        Binary All via the `^` operator.

        This allows to write `Parser1(...) ^ Parser2(...)` instead of `All(Parser1(...), Parser2(...))`

        NOTE: `a ^ b ^ c` is NOT the same as All(a,b,c) as the first will fail if b fails but the second will
        still return `a ^ c`

        Args:
            other: the other parser

        Returns:
            Returns if this and the other parser succeeds at the current location and returns the
            union of all results.
        """
        return All(self, other)

    def where(self, predicate, take_if=True):
        """
        Return a parser that only succeeds if the predicate is true on at least one result of
        a success of this parser.

        Args:
            predicate: the predicate to call on each result which should accept the result and arbitrary
                keyword arguments. The kwargs `context` and `location` are also passed. The predicate
                should return true if a result should get accepted.
            take_if: if False the result is accepted if the predicate function returns False for it

        Returns:
            Success with all the results that have been accepted or Failure if no result was accepted
        """
        return Filter(self, predicate, take_if=take_if)

    def repeat(self, min=1, max=1):
        """
        Return a parser where the current parser is successful at least `min` and at most `max` times.

        `Parser1(...).repeat(min=a, max=b)` is the same as `N(Parser1(...), min=a, max=b)`

        NOTE: this is also the same as `Parser1(...) * (a, b)`

        Args:
            min: minimum number of times the parser must be successful in sequence
            max: maximum number of times the parser may be successfull in sequence

        Returns:
            Parser to match this parser min to max times.
        """
        return N(self, min=min, max=max)

    def __mul__(self, n):
        """
        Return a parser where the current parser is successful n times.

        If n is a tuple (a,b)
        return a parser where the current parser is successful a minimum of a and a maximum of b times.

        `Parser1(...) * (a,b)` is the same as `N(Parser1(...), min=a, max=b)`

        Args:
            n: either an integer used for min and max, or a tuple (min, max)

        Returns:
            Parser to match this parser min to max times.
        """

        if isinstance(n, int):
            return N(self, min=n, max=n)
        elif isinstance(n, tuple) and len(n) == 2:
            return N(self, min=n[0], max=n[1])
        elif isinstance(n, list) and len(n) == 2:
            return N(self, min=n[0], max=n[1])
        else:
            raise Exception("Not an integer or tuple or list of two integers")

    def _make_constraint_predicate(self, matcher, constraint):
        """
        Create predicate that can be used to filter results according to one of the
        annotation-based constraints like .within, .coextensive.

        Args:
            matcher: the annotation matcher
            constraint: the constraint to use on the annotation set

        Returns:
            predicate function

        """

        def _predicate(result, context=None, **kwargs):
            anns = set()
            for d in result.data:
                ann = d.get("ann")
                if ann:
                    anns.add(ann)
            annset = context.annset
            tocall = getattr(annset, constraint)
            annstocheck = tocall(result.span)
            for anntocheck in annstocheck:
                if matcher(anntocheck, context.doc):
                    if anntocheck in anns:
                        continue
                    return True
            return False

        return _predicate

    def _make_notconstraint_predicate(self, matcher, constraint):
        """
        Create predicate that can be used to filter results according to one of the
        annotation-based negated constraints like .notwithin, .notcoextensive.

        Args:
            matcher: the annotation matcher
            constraint: the constraint to use on the annotation set

        Returns:
            predicate function

        """

        def _predicate(result, context=None, **kwargs):
            anns = set()
            for d in result.data:
                ann = d.get("ann")
                if ann:
                    anns.add(ann)
            annset = context.annset
            tocall = getattr(annset, constraint)
            annstocheck = tocall(result.span)
            matched = False
            for anntocheck in annstocheck:
                if matcher(anntocheck, context.doc):
                    if anntocheck in anns:
                        continue
                    matched = True
            return not matched

        return _predicate

    def within(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is within any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match within a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, "covering")
        return Filter(self, pred, matchtype=matchtype)

    def notwithin(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is not within any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match if not within a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, "covering")
        return Filter(self, pred, matchtype=matchtype)

    def coextensive(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is coextensive with
        any annotation that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match when coextensive with a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, "coextensive")
        return Filter(self, pred, matchtype=matchtype)

    def notcoextensive(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is not coextensive
        with any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match if not coextensive with a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, "coextensive")
        return Filter(self, pred, matchtype=matchtype)

    def overlapping(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is overlapping with
        any annotation that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match overlapping with a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, "overlapping")
        return Filter(self, pred, matchtype=matchtype)

    def notoverlapping(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is not overlapping
        within any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match if not overlapping with a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, "overlapping")
        return Filter(self, pred, matchtype=matchtype)

    def covering(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is covering any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match if there is a covering matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, "within")
        return Filter(self, pred, matchtype=matchtype)

    def notcovering(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is not covering
        any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match if not covering a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, "within")
        return Filter(self, pred, matchtype=matchtype)

    def at(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is starting
        at the same offset as an annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match if starting with a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, "startingat")
        return Filter(self, pred, matchtype=matchtype)

    def notat(
        self, type=None, features=None, features_eq=None, text=None, matchtype="first"
    ):
        """
        Parser that succeeds if there is a success for the current parser that is not starting
        with any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match if not starting with a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, "startingat")
        return Filter(self, pred, matchtype=matchtype)

    def before(
        self,
        type=None,
        features=None,
        features_eq=None,
        text=None,
        immediately=False,
        matchtype="first",
    ):
        """
        Parser that succeeds if there is a success for the current parser that is before any annotation
        that matches the given properties.

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            immediately: limit checking to annotations that start right after the end of the current match
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match (immediately) before a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )

        # predicate for this needs to check if there are matching annotations that start at or after
        # the END of the result
        def _predicate(result, context=None, **kwargs):
            anns = set()
            for d in result.data:
                ann = d.get("ann")
                if ann:
                    anns.add(ann)
            annset = context.annset
            if immediately:
                annstocheck = annset.startingat(result.span.end)
            else:
                annstocheck = annset.startingat(result.span.end)
            for anntocheck in annstocheck:
                if matcher(anntocheck, context.doc):
                    if anntocheck in anns:
                        continue
                    return True
            return False

        return Filter(self, _predicate, matchtype=matchtype)

    @support_annotation_or_set
    def notbefore(
        self,
        type=None,
        features=None,
        features_eq=None,
        text=None,
        immediately=False,
        matchtype="first",
    ):
        """
        Parser that succeeds if there is a success for the current parser that is not before any annotation
        that matches the given properties.

        Args:
            type: as for AnnMatcher
            features: as for AnnMatcher
            features_eq: as for AnnMatcher
            text: as for AnnMatcher
            immediately: limit checking to annotations that start right after the end of the current match
            matchtype: matchtype to use for filtering

        Returns:
            Parser modified to only match if not (immediately) before a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )

        def _predicate(result, context=None, **kwargs):
            anns = set()
            for d in result.data:
                ann = d.get("ann")
                if ann:
                    anns.add(ann)
            annset = context.annset
            if immediately:
                annstocheck = annset.startingat(result.span.end)
            else:
                annstocheck = annset.start_ge(result.span.end)
            matched = False
            for anntocheck in annstocheck:
                if matcher(anntocheck, context.doc):
                    if anntocheck in anns:
                        continue
                    matched = True
            return not matched

        return Filter(self, _predicate, matchtype=matchtype)

    def lookahead(self, other):
        """
        Return a parser that only matches the current parser if the given parser can be matched
        afterwards.

        The match of the given parser is not part of the success and does not increment the
        next parsing location.

        Args:
            other: a parser that must match after this parser but the match is discarded.

        Returns:
            a parser that mast be followed by a match of the other parser
        """
        return Lookahead(self, other)


class Lookahead(PampacParser):
    """
    A parser that succeeds for a parser A only if another parser B succeeds right after it.
    However the success of parser B is discarded and does not influence the success nor the
    next parse location.

    If there is more than one result for the success of the parser A, then the result is only
    included in the success if the lookahead parser matches and there is only overall success
    if at least one result remains. This also depends on the matchtype.
    """

    def __init__(self, parser, laparser, matchtype="first"):
        """
        Create a Lookahead parser.

        Args:
            parser: the parser for which to return a success or failure
            laparser:  the parser that must match after the first parser, but it's success is discarded.
            matchtype: which matches to include in the result, one of "first", "longest", "shortest", "all".
        """
        self.parser = parser
        self.laparser = laparser
        self.matchtype = matchtype

    def parse(self, location, context):
        ret = self.parser.parse(location, context).issuccess()
        if ret.issuccess():
            res = ret.result(self.matchtype)
            if isinstance(res, list):
                # we need to check each of the results
                allres = []
                for r in res:
                    newlocation = r.location
                    laret = self.laparser.parse(newlocation, context)
                    if laret.issuccess():
                        allres = []
                if len(allres) > 0:
                    return Success(results=allres, context=context)
                else:
                    return Failure(
                        context=context,
                        message="Lookahead failed for all results",
                        location=location,
                    )
            else:
                newlocation = res.location
                laret = self.laparser.parse(newlocation, context)
                if laret.issuccess():
                    return ret
                else:
                    return Failure(
                        context=context, message="Lookahead failed", location=location
                    )
        else:
            return ret


class Filter(PampacParser):
    """
    Select only some of the results returned by a parser success, call the predicate function on each to check.
    This can also be used to check a single result and decide if it should be a success or failure.
    """

    def __init__(self, parser, predicate, take_if=True, matchtype="first"):
        """
        Invoke predicate with each result of a successful parse of parser and return success with the remaining
        list. If the remaining list is empty, return Failure.

        Args:
            parser: the parser to use
            predicate: the function to call for each result of the parser success
            take_if: if True takes if predicate returns True, otherwise if predicate returns false
            matchtype: how to choose among all the selected results
        """
        self.parser = parser
        self.predicate = predicate
        self.take_if = take_if
        self.matchtype = matchtype

    def parse(self, location, context):
        ret = self.parser.parse(location, context)
        if ret.issuccess():
            res = []
            for r in ret:
                if (
                    self.predicate(r, context=context, location=location)
                    == self.take_if
                ):
                    res.append(r)
            if len(res) == 0:
                return Failure(
                    context=context,
                    location=location,
                    message="No result satisfies predicate",
                )
            else:
                return Success(res, context=context)
        else:
            return ret


class Call(PampacParser):
    """
    A parser that calls a function on success (and optionally on failure).

    This parser is identical to the original parser but calls the given function
    on success. The function must accept the success instance and arbitrary keyword arguments.
    The kwargs `context`, `location`, `name` and `parser` are passed on.

    If the `onfailure` parameter is not none, this is a function that is called on Failure with the
    Failure instance and the same kwargs.

    The parsing result of this parser is the same as the parsing result of the original parser.
    """

    def __init__(self, parser, func, onfailure=None):
        """
        Create a Call parser.

        Args:
            parser: the original parser to use
            func:  the function to call if the original parser returns success
            onfailure: the function to call if the original parser returns failure
        """
        self.parser = parser
        self.func = func
        self.onfailure = onfailure

    def parse(self, location, context):
        ret = self.parser.parse(location, context)
        if ret.issuccess():
            self.func(
                ret,
                context=context,
                location=location,
                name=self.parser.name,
                parser=self.parser.__class__.__name__,
            )
        else:
            if self.onfailure:
                self.onfailure(
                    ret,
                    context=context,
                    location=location,
                    name=self.parser.name,
                    parser=self.parser.__class__.__name__,
                )
        return ret


class _AnnBase(PampacParser):
    """
    Common base class with common methods for both Ann and AnnAt.
    """

    def gap(self, min=0, max=0):
        """
        Return a parser which only matches self if the next annotation offset starts at this distance
        from the current next text offset.

        Args:
            min: minimum gap size (default: 0)
            max: maximum gap size (default: 0)

        Returns:
            parser that tries to match only if the next annotation is within the gap range
        """

        def _parse(location, context):
            ann = context.get_ann(location.ann_location)
            if ann is None:
                return Failure(
                    context=context, location=location, message="No annotation left"
                )
            if (
                ann.start >= location.text_location + min
                and ann.start <= location.text_location + max
            ):
                return self.parse(location, context)
            else:
                return Failure(
                    context=context,
                    location=location,
                    message="Next ann not withing gap",
                )

        return PampacParser(parser_function=_parse)

    def findgap(self, min=0, max=0):
        """
        Return a parser which matches at the next location where an annotation satisfies the gap constraint
        with respect to the current text location.

        Args:
            min: minimum gap size (default 0)
            max: maximum gap size (default 0)

        Returns:
            parser that tries to match at the next annotation found within the gap range
        """

        def _parse(location, context):
            idx = location.ann_location
            while True:
                ann = context.get_ann(idx)
                if ann is None:
                    return Failure(
                        context=context, location=location, message="No annotation left"
                    )
                if (
                    ann.start >= location.text_location + min
                    and ann.start <= location.text_location + max
                ):
                    return self.parse(location, context)
                if ann.ann.start > location.text_location + max:
                    return Failure(
                        context=context,
                        location=location,
                        message="No annotation found withing gap",
                    )
                idx + 1

        return PampacParser(parser_function=_parse)


class AnnAt(_AnnBase):
    """
    Parser for matching the first or all annotations at the offset for the next annotation in the list.
    """

    def __init__(
        self,
        type=None,
        features=None,
        features_eq=None,
        text=None,
        matchtype="first",
        name=None,
        useoffset=True,
    ):
        """
        Create an AnnAt parser.

        Args:
            type: the type to match, can be None, a string, a regular expression or a callable
            features: the features that must be matched, a dictionary as the FeatureMatcher arguments
            features_eq: the features that must be matched and no other features may exist, a dictionary as
               the FeatureEqMatcher arguments.
            text: the covered document text to match
            matchtype: which matches to return in a success, one of "all", "first" (default), "longest", "shortest"
            name: the name of the match. If specified, a dictionary describing the match is added to the result.
            useoffset: if True, tries to match at the current text offset, not the start offset of the
                next annotation to match.
        """
        self.type = type
        self.features = features
        self.features_eq = features_eq
        self.text = text
        self.name = name
        self._matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        self.matchtype = matchtype
        self.useoffset = useoffset

    def parse(self, location, context):
        if self.useoffset:
            location = context.update_location_byoffset(location)
        next_ann = context.get_ann(location)
        if not next_ann:
            return Failure(
                context=context,
                location=location,
                parser=self.__class__.__name__,
                message="No annotation left",
            )
        results = []
        start = next_ann.start
        matched = False
        while True:
            if self._matcher(next_ann):
                matched = True
                matchlocation = Location(
                    text_location=start, ann_location=location.ann_location
                )
                if self.name is None:
                    data = None
                else:
                    data = dict(
                        span=Span(next_ann),
                        location=matchlocation,
                        ann=next_ann,
                        name=self.name,
                    )
                # update location
                location = context.inc_location(location, by_index=1)
                result = Result(
                    data=data,
                    location=location,
                    span=Span(next_ann.start, next_ann.end),
                )
                if self.matchtype == "first":
                    return Success(result, context)
                results.append(result)
                next_ann = context.get_ann(location)
                if not next_ann or next_ann.start != start:
                    break
            else:
                location = context.inc_location(location, by_index=1)
                next_ann = context.get_ann(location)
                if not next_ann or next_ann.start != start:
                    break
        if not matched:
            return Failure(
                context=context,
                parser=self.__class__.__name__,
                location=location,
                message="No matching annotation",
            )
        else:
            res = Success.select_result(results, matchtype=self.matchtype)
            return Success(res, context)


class Ann(_AnnBase):
    """
    Parser for matching the next annotation in the annotation list.
    """

    def __init__(
        self,
        type=None,
        features=None,
        features_eq=None,
        text=None,
        name=None,
        useoffset=True,
    ):
        """

        Args:
            type: (default: None): type to match, string, regexp or predicate function
            features: (default: None): features to match, dictionary where each value is value, regexp or predicate function
               Annotation can contain additional features.
            features_eq: (default: None): features to match, annotation must not contain additional features
            text: (default: None): document text to match, string or regexp
            name: (default: None): if set to a non-empty string, saves the data and assigns that name to the data
            useoffset: if True, and a location is give where the next annotation starts before the text offset, skips
               forward in the annotation list until an annotation is found at or after that offset.
               If no such annotation found, fails. If False, always uses the next annotation in the list, no matter
               the offset.
        """
        self.type = type
        self.features = features
        self.features_eq = features_eq
        self.text = text
        self.name = name
        self.useoffset = useoffset
        self._matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )

    def parse(self, location, context):
        if self.useoffset:
            location = context.update_location_byoffset(location)
        next_ann = context.get_ann(location)
        if not next_ann:
            return Failure(
                context=context,
                parser=self.__class__.__name__,
                location=location,
                message="No annotation left",
            )
        # try to match it
        if self._matcher(next_ann, doc=context.doc):
            newlocation = context.inc_location(location, by_index=1)
            if self.name is not None:
                data = dict(
                    span=Span(next_ann),
                    location=location,
                    ann=next_ann,
                    name=self.name,
                )
            else:
                data = None
            span = Span(next_ann.start, next_ann.end)
            return Success(Result(data=data, span=span, location=newlocation), context)
        else:
            return Failure(
                location=location, context=context, parser=self.__class__.__name__
            )


class Find(PampacParser):
    """
    A parser that tries another parser at successive offsets or annotations until it matches
    the end of the document / parsing range is reached.
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
            ret = self.parser.parse(location, context)
            if ret.issuccess():
                return ret
            else:
                if self.by_anns:
                    location = context.inc_location(location, by_index=1)
                    if context.at_endofanns(location):
                        return Failure(
                            context=context,
                            message="Not found via anns",
                            location=location,
                        )
                else:
                    location = context.inc_location(location, by_offset=1)
                    if context.at_endoftext(location):
                        return Failure(
                            context=context,
                            message="Not found via text",
                            location=location,
                        )


class Text(PampacParser):
    """
    A parser that matches some text or regular expression.
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
        location = context.update_location_byindex(location)
        txt = context.doc.text[location.text_location:]
        if isinstance(self.text, CLASS_RE_PATTERN) or isinstance(
            self.text, CLASS_REGEX_PATTERN
        ):
            m = self.text.match(txt)
            if m:
                lengrp = len(m.group())
                newlocation = context.inc_location(location, by_offset=lengrp)
                if self.name:
                    data = dict(
                        location=location,
                        span=Span(
                            location.text_location,
                            location.text_location + len(m.group()),
                        ),
                        text=m.group(),
                        groups=m.groups(),
                        name=self.name,
                    )
                else:
                    data = None
                span = Span(
                    location.text_location, location.text_location + len(m.group())
                )
                return Success(
                    Result(data=data, location=newlocation, span=span), context
                )
            else:
                return Failure(context=context)
        else:
            if not self.matchcase:
                txt = txt.upper()
            if txt.startswith(self.text):
                if self.name:
                    data = dict(
                        span=Span(
                            location.text_location,
                            location.text_location + len(self.text),
                        ),
                        location=location,
                        text=self.text,
                        name=self.name,
                    )
                else:
                    data = None
                newlocation = context.inc_location(location, by_offset=len(self.text))
                span = Span(
                    location.text_location, location.text_location + len(self.text)
                )
                return Success(
                    Result(data=data, location=newlocation, span=span), context
                )
            else:
                return Failure(context=context)


class Or(PampacParser):
    """
    Create a parser that accepts the first seccessful one of all the parsers specified.
    """

    def __init__(self, *parsers, matchtype="all"):
        """
        Creates a parser that tries each of the given parsers in order and uses the first
        one that finds a successful match.

        Args:
            *parsers: two or more parsers to each try in sequence
            matchtype: which of the results from the successful parser to return.
        """
        assert len(parsers) > 1
        self.parsers = parsers
        self.matchtype = matchtype

    def parse(self, location, context):
        for p in self.parsers:
            ret = p.parse(location, context)
            if ret.issuccess():
                if self.matchtype == "all":
                    return ret
                result = ret.result(self.matchtype)
                newloc = result.location
                return Success(
                    Result(result.data, location=newloc, span=result.span), context
                )
        return Failure(
            context=context, location=location, message="None of the choices match"
        )


class And(PampacParser):
    """
    Return a parser that is successful if all the parsers match at some location, and
    fails otherwise. Success always contains all results from all parsers.
    """

    def __init__(self, *parsers):
        """
        Create an And parser.

        Args:
            *parsers: a list of two or more parsers.
        """
        assert len(parsers) > 1
        self.parsers = parsers

    def parse(self, location, context):
        results = []
        for p in self.parsers:
            ret = p.parse(location, context)
            if ret.issuccess():
                for r in ret:
                    results.append(r)
            else:
                return Failure(
                    context=context,
                    location=location,
                    message="Not all parsers succeed",
                )
        return Success(results)


class All(PampacParser):
    """
    Return a parser that succeeds if one or more parsers succeed at some location.
    If success, all results from all succeeding parsers are included.
    """

    def __init__(self, *parsers):
        """
        Create an All parser.

        Args:
            *parsers: list of two ore more parsers.
        """
        assert len(parsers) > 1
        self.parsers = parsers

    def parse(self, location, context):
        results = []
        for p in self.parsers:
            ret = p.parse(location, context)
            if ret.issuccess():
                for r in ret:
                    results.append(r)
        if len(results) > 0:
            return Success(results)
        else:
            return Failure(
                context=context,
                location=location,
                message="None of the parsers succeeded",
            )


class Seq(PampacParser):
    """
    A parser that represents a sequence of matching parsers. Each result of this parser combines
    all the data from the sequence element parsers. For matchtype all and select all, all paths
    through all the possible ways to match the sequence get combined into separate results of
    a successful parse.
    """

    def __init__(self, *parsers, matchtype="first", select="first", name=None):
        """

        Args:
            *parsers: two or more parsers
            matchtype: (default "first") one of "first", "longest", "shortest", "all": which match to return.
              Note that even if a matchtype for a single match is specified, the parser may still need to
              generate an exponential number of combinations for all the results to select from.
            select: (default "first") one of "first", "longest", "shortest", "all": which match to choose from each
              of the parsers. Only if "all" is used will more than one result be generated.
            name: if not None, a separate data element is added to the result with that name and
              a span that represents the span of the result.
        """
        assert len(parsers) > 1
        self.parsers = parsers
        if matchtype is None:
            matchtype = "first"
        assert matchtype in ["first", "longest", "shortest", "all"]
        self.select = select
        self.matchtype = matchtype
        self.name = name

    def parse(self, location, context):
        if self.select != "all":
            datas = []
            first = True
            start = None
            end = None
            for parser in self.parsers:
                ret = parser.parse(location, context)
                if ret.issuccess():
                    result = ret.result(self.select)
                    for d in result.data:
                        datas.append(d)
                    location = result.location
                    if first:
                        first = False
                        start = result.span.start
                    end = result.span.end
                else:
                    return Failure(
                        context=context, location=location, message="Mismatch in Seq"
                    )
            if self.name:
                datas.append(
                    dict(span=Span(start, end), name=self.name, location=location)
                )
            return Success(
                Result(data=datas, location=location, span=Span(start, end)), context
            )
        else:
            # This does a depth-first enumeration of all matches: each successive parser gets tried
            # for each result of the previous one.

            def depthfirst(lvl, result):
                parser = self.parsers[lvl]
                ret = parser.parse(result.location, context)
                if ret.issuccess():
                    for res in ret:
                        datas = result.data.copy()
                        for d in res.data:
                            datas.append(d)
                        loc = res.location
                        span = Span(location.text_location, res.location.text_location)
                        if lvl == len(self.parsers) - 1:
                            if self.name:
                                datas.append(
                                    dict(
                                        span=Span(start, end),
                                        location=loc,
                                        name=self.name,
                                    )
                                )
                            newresult = Result(datas, location=loc, span=span)
                            yield newresult
                        else:
                            newresult = Result(datas, location=loc, span=span)
                            yield from depthfirst(lvl + 1, newresult)

            gen = depthfirst(0, Result(data=[], location=location, span=Span(0, 0)))
            all = []
            best = None
            for idx, result in enumerate(gen):
                if self.matchtype == "first" and idx == 0:
                    return Success(result, context)
                if self.matchtype == "all":
                    all.append(result)
                elif self.matchtype == "longest":
                    if best is None:
                        best = result
                    elif result.span.end > best.span.end:
                        best = result
                elif self.matchtype == "shortest":
                    if best is None:
                        best = result
                    elif result.span.end < best.span.end:
                        best = result
            if self.matchtype == "all":
                if len(all) > 0:
                    return Success(all, context)
                else:
                    return Failure(context=context, location=location)
            else:
                if best is not None:
                    return Success(best, context)
                else:
                    return Failure(context=context, location=location)


class N(PampacParser):
    """
    A parser that represents a sequence of k to l matching parsers.

    If no until parser is given, the parser matches greedily as many times as possible.
    The until parser can be used to make the matching stop as soon as the until parser succeeds.
    """

    def __init__(
        self,
        parser,
        min=1,
        max=1,
        matchtype="first",
        select="first",
        until=None,
        name=None,
    ):
        """
        Return a parser that matches min to max matches of parser in sequence. If until is specified, that
        parser is tried to match before each iteration and as soon as it matched, the parser succeeds.
        If after ming to max matches of the parser, until does not match, the parser fails.

        Args:
            parser: the parser that should match min to max times
            min: minimum number of times to match for a success
            max: maximum number of times to match for a success
            matchtype: which results to include in a successful match, one of first, longest, shortest, all
            until: parser that terminates the repetition
            name: if not None, adds an additional data element to the result which contains the
              and span of the whole sequence.
        """
        self.parser = parser
        self.min = min
        self.max = max
        self.matchtype = matchtype
        self.until = until
        self.select = select
        self.name = name

    def parse(self, location, context):
        start = location.text_location
        end = start
        if self.select != "all":
            datas = []
            i = 0
            first = True
            # location is the location where we try to match
            while True:
                if self.until and i >= self.min:
                    ret = self.until.parse(location, context)
                    if ret.issuccess():
                        res = ret.result(self.select)
                        data = res.data
                        for d in data:
                            datas.append(d)
                        loc = res.location
                        end = res.span.end
                        if self.name:
                            datas.append(
                                dict(
                                    span=Span(start, end), location=loc, name=self.name
                                )
                            )
                        return Success(
                            Result(datas, location=loc, span=Span(start, end)), context
                        )
                ret = self.parser.parse(location, context)
                if not ret.issuccess():
                    if i < self.min:
                        return Failure(
                            context=context,
                            location=location,
                            message=f"Not at least {self.min} matches",
                        )
                    else:
                        if self.name:
                            datas.append(
                                dict(
                                    span=Span(start, end),
                                    location=location,
                                    name=self.name,
                                )
                            )
                        return Success(
                            Result(
                                data=datas, location=location, span=Span(start, end)
                            ),
                            context,
                        )
                else:
                    result = ret.result(self.select)
                    if first:
                        first = False
                        start = result.span.start
                    end = result.span.end
                    data = result.data
                    for d in data:
                        datas.append(d)
                    location = result.location
                    i += 1
                    if i == self.max:
                        break
            if self.until:
                ret = self.until.parse(location, context)
                if ret.issuccess():
                    res = ret.result(self.select)
                    data = res.data
                    loc = res.location
                    end = res.span.end
                    for d in data:
                        datas.append(d)
                    if self.name:
                        datas.append(
                            dict(span=Span(start, end), location=loc, name=self.name)
                        )
                    return Success(
                        Result(datas, location=loc, span=Span(start, end)), context
                    )
                else:
                    return Failure(
                        context=context,
                        location=location,
                        message="Until parser not successful",
                    )
            if self.name:
                datas.append(
                    dict(span=Span(start, end), location=location, name=self.name)
                )
            return Success(
                Result(data=datas, location=location, span=Span(start, end)), context
            )
        else:
            # This does a depth-first enumeration of all matches: each successive parser gets tried
            # for each result of the previous one.
            def depthfirst(lvl, result):
                # if we already have min matches and we can terminate early, do it
                if self.until and lvl >= self.min:
                    ret = self.until.parse(result.location, context)
                    if ret.issuccess():
                        for res in ret:
                            data = result.data.copy()
                            for dtmp in res.data:
                                data.append(dtmp)
                            loc = res.location
                            end = res.span.end
                            if self.name:
                                data.append(
                                    dict(
                                        span=Span(start, end),
                                        location=location,
                                        name=self.name,
                                    )
                                )
                            yield Result(data, location=loc, span=Span(start, end))
                            return
                # if we got here after the max number of matches, and self.until is set, then
                # the parse we did above did not succeed, so we end without a result
                if self.until and lvl > self.max:
                    return
                # if we got here after the max number of matches and self.util is not set, we
                # can yield the current result as we found max matches
                if lvl >= self.max:
                    yield result
                    return
                # lvl is still smaller than max, so we try to match more
                ret = self.parser.parse(result.location, context)
                if ret.issuccess():
                    # for each of the results, try to continue matching
                    for res in ret:
                        datas = result.data.copy()
                        for d in res.data:
                            datas.append(d)
                        loc = res.location
                        span = Span(location.text_location, res.location.text_location)
                        newresult = Result(datas, location=loc, span=span)
                        yield from depthfirst(lvl + 1, newresult)
                else:
                    if lvl <= self.min:
                        return
                    else:
                        # we already have at least min matches: if we have no until, we can yield the result
                        if not self.until:
                            data = result.data
                            end = result.span.end
                            if self.name:
                                data.append(
                                    dict(
                                        span=Span(start, end),
                                        location=result.location,
                                        name=self.name,
                                    )
                                )
                            yield result
                        else:
                            # if we have until, then the until above did not match so neither the normal parser
                            # nor the until did match so we do not have a success
                            return

            gen = depthfirst(0, Result(data=[], location=location, span=(None, None)))
            all = []
            best = None
            for idx, result in enumerate(gen):
                if self.matchtype == "first" and idx == 0:
                    return Success(result, context)
                if self.matchtype == "all":
                    all.append(result)
                elif self.matchtype == "longest":
                    if best is None:
                        best = result
                    elif result.span.end > best.span.end:
                        best = result
                elif self.matchtype == "shortest":
                    if best is None:
                        best = result
                    elif result.span.end < best.span.end:
                        best = result
            if self.matchtype == "all":
                if len(all) > 0:
                    return Success(all, context)
                else:
                    return Failure(context=context, location=location)
            else:
                if best is not None:
                    return Success(best, context)
                else:
                    return Failure(context=context, location=location)


class Rule(PampacParser):
    """
    A matching rule: this defines the parser and some action (a function) to carry out if the rule matches
    as it is tried as one of many rules with a Pampac instance. Depending on select setting for pampac
    the action only fires under certain circumstances (e.g. the rule is the first that matches at a location).
    Rule is thus different from pattern.call() or Call(pattern, func) as these always call the function if
    there is a successful match.
    """

    def __init__(self, parser, action, priority=0):
        """
        Create a Rule.

        Args:
            parser: the parser to match for the rule
            action:  the action to perform, or a function to call
            priority: the priority of the rule
        """
        self.parser = parser
        self.action = action
        self.priority = priority

    def set_priority(self, val):
        """
        Different way of setting the priority.
        """
        self.priority = val
        return self

    def parse(self, location, context):
        """
        Return the parse result. This does NOT automatically invoke the action if the parse result is a success.
        The invoking Pampac instance decides, based on its setting, for which matching rules the action is
        actually carried out.

        Returns:
            Success or failure of the parser

        """
        return self.parser.parse(location, context)


class Pampac:
    """
    A class for applying a sequence of rules to a document.
    """

    def __init__(self, *rules, skip="longest", select="first"):
        """
        Initialize Pampac.

        Args:
            *rules: one or more rules
            skip:  how proceed after something has been matched at a position. One of: "longest" to proceed
              at the next text offset after the end of the longest match. "next" to use a location with the highest
              text and annotation index over all matches. "one" to increment the text offset by one and adjust
              the annotation index to point to the next annotation at or after the new text offset.
              "once": do not advance after the first location where a rule matches. NOTE: if skipping depends on
              on the match(es), only those matches for which a rule fires are considered.
            select: which of those rules that match to actually apply, i.e. call the action part of the rule.
              One of: "first": try all rules in sequence and call only the first one that matches. "highest": try
              all rules and only call the rules which has the highest priority, if there is more than one, the first
              of those.
        """
        assert len(rules) > 0
        assert skip in ["one", "longest", "next", "once"]
        assert select in ["first", "highest", "all"]
        for r in rules:
            assert isinstance(r, Rule)
        self.rules = rules
        self.priorities = [r.priority for r in self.rules]
        self.max_priority = max(self.priorities)
        for idx, r in enumerate(rules):
            if r.priority == self.max_priority:
                self.hp_rule = r
                self.hp_rule_idx = idx
                break
        self.skip = skip
        self.select = select

    def set_skip(self, val):
        """
        Different way to set the skip parameter.
        """
        self.skip = val
        return self

    def set_select(self, val):
        """
        Different way to set the select parameter.
        """
        self.select = val
        return self

    def run(self, doc, annotations, outset=None, start=None, end=None, debug=False):
        """
        Run the rules from location start to location end (default: full document), using the annotation set or list.

        Args:
            doc: the document to run on
            annotations: the annotation set or iterable to use
            outset: the output annotation set. If this is a string, retrieves the set from doc
            start: the text offset where to start matching
            end: the text offset where to end matching

        Returns:
            a list of tuples (offset, actionreturnvals) for each location where one or more matches occurred
        """
        logger = init_logger(debug=debug)
        if isinstance(outset, str):
            outset = doc.annset(outset)
        ctx = Context(doc=doc, anns=annotations, outset=outset, start=start, end=end)
        returntuples = []
        location = Location(ctx.start, 0)
        while True:
            # try the rules at the current position
            cur_offset = location.text_location
            frets = []
            rets = dict()
            for idx, r in enumerate(self.rules):
                logger.debug(f"Trying rule {idx} at location {location}")
                ret = r.parse(location, ctx)
                if ret.issuccess():
                    rets[idx] = ret
                    logger.debug(f"Success for rule {idx}, {len(ret)} results")
                    if self.select == "first":
                        break
            # we now got all the matching results in rets
            # if we have at least one matching ...
            if len(rets) > 0:
                fired_rets = []
                # choose the rules to fire and call the actions
                if self.select == "first":
                    idx, ret = list(rets.items())[0]
                    logger.debug(f"Firing rule {idx} at {location}")
                    fret = self.rules[idx].action(ret, context=ctx, location=location)
                    frets.append(fret)
                    fired_rets.append(ret)
                elif self.select == "all":
                    for idx, ret in rets.items():
                        logger.debug(f"Firing rule {idx} at {location}")
                        fret = self.rules[idx].action(
                            ret, context=ctx, location=location
                        )
                        frets.append(fret)
                        fired_rets.append(ret)
                elif self.select == "highest":
                    for idx, ret in rets.items():
                        if idx == self.hp_rule_idx:
                            logger.debug(f"Firing rule {idx} at {location}")
                            fret = self.rules[idx].action(
                                ret, context=ctx, location=location
                            )
                            frets.append(fret)
                            fired_rets.append(ret)
                # now that we have fired rules, find out how to advance to the next position
                if self.skip == "once":
                    return frets
                elif self.skip == "once":
                    location = ctx.inc_location(location, by_offset=1)
                elif self.skip == "longest":
                    longest = 0
                    for ret in fired_rets:
                        for res in ret:
                            if res.location.text_location > longest:
                                longest = res.location.text_location
                    location.text_location = longest
                    location = ctx.update_location_byoffset(location)
                elif self.skip == "next":
                    for ret in fired_rets:
                        for res in ret:
                            if res.location.text_location > location.text_location:
                                location.text_location = res.location.text_location
                                location.ann_location = res.location.ann_location
                            elif (
                                res.location.text_location == location.text_location
                                and res.location.ann_location > location.ann_location
                            ):
                                location.ann_location = res.location.ann_location
                returntuples.append((cur_offset, frets))
            else:
                # we had no match, just continue from the next offset
                location = ctx.inc_location(location, by_offset=1)
            if ctx.at_endofanns(location) or ctx.at_endoftext(location):
                break
        return returntuples

    __call__ = run


def _get_data(succ, name, resultidx=0, dataidx=0, silent_fail=False):
    """
    Helper method to return the data for the given result index and name, or None.

    Args:
        succ: success instance
        name: name of the data
        resultidx: index of the result in success
        dataidx: if there is more than one matching data with that name, which one to return
        silent_fail: if True, return None, if False, raise an exception if the data is not present

    Returns:
        the data or None

    """
    if resultidx >= len(succ):
        if not silent_fail:
            raise Exception(f"No resultidx {resultidx}, only {len(succ)} results")
        else:
            return
    res = succ[resultidx]
    data = res.data4name(name)
    if not data:
        if not silent_fail:
            raise Exception(f"No data with name {name} in result")
        else:
            return
    if dataidx >= len(data):
        if not silent_fail:
            raise Exception(f"No data with index {dataidx}, length is {len(data)}")
        else:
            return
    return data[dataidx]


# ACTIONS:


class AddAnn:
    """
    Action for adding an annotation.
    """

    def __init__(
        self,
        name=None,
        ann=None,  # create a copy of this ann retrieved with GetAnn
        anntype=None,  # or create a new annotation with this type
        annset=None,  # if not none, create in this set instead of the one used for matching
        features=None,
        span=None,  # use literal span, GetSpan, if none, span from match
        resultidx=0,
        dataidx=0,
        silent_fail=False,
    ):
        """
        Create an action for adding a new annotation to the outset.

        Args:
            name: the name of the match to use for getting the annotation span
            ann:  either an Annotation which will be (deep) copied to create the new annotation, or
                a GetAnn helper for copying the annoation the helper returns. If this is specified the
                other parameters for creating a new annotation are ignored.
            anntype: the type of a new annotation to create
            annset: if not None, create the new annotation in this set instead of the one used for matching
            features: the features of a new annotation to create. This can be a GetFeatures helper for copying
                the features from another annotation in the results
            span: the span of the annotation, this can be a GetSpan helper for copying the span from another
                annotation in the results
            resultidx: the index of the result to use if more than one result is in the Success
            dataidx: the index of the data item to use if more than one item matches the given name
            silent_fail: if True and the annotation can not be created for some reason, just do silently nothing,
                otherwise raises an Exception.
        """
        # span is either a span, the index of data to take the span from, or a callable that will return the
        # span at firing time
        assert name
        assert anntype is not None or ann is not None
        self.name = name
        self.anntype = anntype
        self.ann = ann
        self.features = features
        self.span = span
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.silent_fail = silent_fail
        self.annset = annset

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        span = data["span"]
        if self.annset:
            outset = self.annset
        else:
            outset = context.outset
        if self.ann:
            if isinstance(self.ann, Annotation):
                outset.add_ann(self.ann.deepcopy())
            else:
                ann = self.ann(succ)
                if ann is None:
                    if self.silent_fail:
                        return
                    else:
                        raise Exception("No matching annotation found")
                outset.add_ann(ann)
        else:
            if self.span:
                if callable(self.span):
                    span = self.span(succ, context=context, location=location)
                else:
                    span = self.span
            if callable(self.anntype):
                anntype = self.anntype(succ, context=context, location=location)
            else:
                anntype = self.anntype
            if self.features:
                if callable(self.features):
                    features = self.features(succ, context=context, location=location)
                else:
                    features = self.features
            else:
                features = None
            outset.add(span.start, span.end, anntype, features=features)


class UpdateAnnFeatures:
    """
    Action for updating the features of an annotation.
    """

    def __init__(
        self,
        name,
        ann=None,
        features=None,
        replace=False,  # replace existing features rather than updating
        resultidx=0,
        dataidx=0,
        silent_fail=False,
    ):
        """
        Create an UpdateAnnFeatures action.

        Args:
            name: the name of the match to use for getting the annotation span
            ann: if specified use the features from this annotation. This can be either a literal annotation
                or a GetAnn helper to access another annotation from the result.
            features: the features to use for updating, either literal  features or a GetFeatures helper.
            replace: if True, replace the existing features with the new ones, otherwise update the existing features.
            resultidx: the index of the result to use, if there is more than one
            dataidx: the index of a matching data element to use, if more than one matches the given name
            silent_fail: if True, do not raise an exception if the features cannot be updated
        """
        # span is either a span, the index of data to take the span from, or a callable that will return the
        # span at firing time
        assert isinstance(ann, GetAnn)
        assert features is not None
        self.name = name
        self.ann = ann
        self.replace = replace
        self.features = features
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        if not data:
            if self.silent_fail:
                return
            else:
                raise Exception(f"Could not find the name {self.name}")
        theann = data.get("ann")
        if theann is None:
            if self.silent_fail:
                return
            else:
                raise Exception(
                    f"Could not find an annotation for the name {self.name}"
                )
        if isinstance(self.ann, Annotation):
            feats = deepcopy(self.ann.features)
        else:
            ann = self.ann(succ)
            if ann is None:
                if self.silent_fail:
                    return
                else:
                    raise Exception("No matching annotation found")
            feats = deepcopy(ann.features)
        if not feats and callable(self.features):
            feats = self.features(succ, context=context, location=location)
        elif not feats:
            feats = deepcopy(self.features)
        if self.replace:
            theann.features.clear()
        theann.features.update(feats)


class RemoveAnn:
    def __init__(self, name, ann=None, annset=None, resultidx=0, dataidx=0, which="first", silent_fail=True):
        pass

    def __call__(self, succ, context=None, location=None):
        pass



# GETTERS


class GetAnn:
    """
    Helper to access an annoation from a match with the given name.
    """

    def __init__(self, name, resultidx=0, dataidx=0, silent_fail=False):
        """
        Create a GetAnn helper.

        Args:
            name: the name of the match to use.
            resultidx:  the index of the result to use if there is more than one.
            dataidx:  the index of the data element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None.
        """
        self.name = name
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        ann = data.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.dataidx}"
                )
        return ann


class GetFeatures:
    """
    Helper to access the features of an annotation in a match with the given name.
    """

    def __init__(self, name, resultidx=0, dataidx=0, silent_fail=False):
        """
        Create a GetFeatures helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            dataidx:  the index of the data element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        ann = data.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.dataidx}"
                )
        return ann.features


class GetType:
    """
    Helper to access the type of an annotation in a match with the given name.
    """

    def __init__(self, name, resultidx=0, dataidx=0, silent_fail=False):
        """
        Create a GetType helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            dataidx:  the index of the data element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        ann = data.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.dataidx}"
                )
        return ann.type


class GetStart:
    """
    Helper to access the start offset of the annotation in a match with the given name.
    """

    def __init__(self, name, resultidx=0, dataidx=0, silent_fail=False):
        """
        Create a GetStart helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            dataidx:  the index of the data element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        span = data["span"]
        return span.start


class GetEnd:
    """
    Helper to access the end offset of the annotation in a match with the given name.
    """

    def __init__(self, name, resultidx=0, dataidx=0, silent_fail=False):
        """
        Create a GetEnd helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            dataidx:  the index of the data element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        span = data["span"]
        return span.end


class GetFeature:
    """
    Helper to access the features of the annotation in a match with the given name.
    """

    def __init__(self, name, featurename, resultidx=0, dataidx=0, silent_fail=False):
        """
        Create a GetFeatures helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            dataidx:  the index of the data element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.silent_fail = silent_fail
        self.featurename = featurename

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        ann = data.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.dataidx}"
                )
        return ann.features.get(self.featurename)


class GetText:
    """
    Helper to access text, either covered document text of the annotation or matched text.
    """

    def __init__(self, name, resultidx=0, dataidx=0, silent_fail=False):
        """
        Create a GetText helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            dataidx:  the index of the data element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        span = data.get("span")
        if span:
            return context.doc[span]
        else:
            if self.silent_fail:
                return
            else:
                raise Exception("Could not find a span for data")


class GetRegexGroup:
    """
    Helper to access the given regular expression matching group in a match with the given name.
    """

    def __init__(self, name, group=0, resultidx=0, dataidx=0, silent_fail=False):
        """
        Create a GetText helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            dataidx:  the index of the data element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.dataidx = dataidx
        self.group = group
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        data = _get_data(
            succ, self.name, self.resultidx, self.dataidx, self.silent_fail
        )
        groups = data.get("groups")
        if groups:
            return groups[self.group]
        else:
            if self.silent_fail:
                return
            else:
                raise Exception("Could not find regexp groups for data")
