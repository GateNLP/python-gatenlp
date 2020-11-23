"""
Module for PAMPAC (Pattern Matching wit PArser Combinators) which allows to create parsers that can match
patterns in annotations and text and carry out actions if a match occurs.

NOTE: this implementation has been inspired by https://github.com/google/compynator
"""
import functools
from collections.abc import Iterable, Sized
from .matcher import AnnMatcher, CLASS_REGEX_PATTERN, CLASS_RE_PATTERN
from gatenlp.utils import support_annotation_or_set
from gatenlp import AnnotationSet

# TODO: check that Context.end is respected with all individual parsers: we should not match beyond that offset!

# TODO: figure out which parser parameters could be implemented as parser modifiers instead/in addition???

# TODO: implement backreferences: as a parser and modifier: equality of some part of the current data with
# HOW??? to get access to all existing data so far: Need to change things so that all parsers which
# produce an actual sequence invoke the next parser with the result so far as additional (optional?) parameter.
# so we need to change the parse method.
# the same part of some existing named data (nth named data).
# e.g. Backref(parser, to_name=name, to_n=1/-1, to_field="text", eq=None, predicate=None)
# to_name: the name of the data, if not exists, fail
# to_n: the nth data with that name, if negate the nth from the end, if not exist, fail
# to_field: the field of the data dict, if not exists, fail
# eq: how to compare, if None use normal equality
# predicate: a function x,y where x is all existing data and y is the data of parser



# TODO: IMPORTANT: the advancing strategy for rules could be different and more flexible from the way how we match sequences
# within a rule, maybe?

# TODO: think about rule priorities and matching styles similar to JAPE:
# if several rules match at the same location, which one should be "fired"?
# appelt style: use longest match, if more than one, use highest priority, if more than one with same p, use first
#   after matching, advance to next position in document after the match
# all style: use all matches, advance to next position in document (next offset)
# brill style: use all matches, advance to position after longest match
# first: no direct correspondence but we could just use the first rule in the list of rules
# once: match once, then do not advance and repeat.


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
        Creata parser result.

        Args:
            data: the data associated with the result, this should be a dictionary or None.
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
        return f"Result(loc={self.location},span=({self.span[0]},{self.span[1]}),ndata={len(self.data)})"

    def __repr__(self):
        return f"Result(loc={self.location},span=({self.span[0]},{self.span[1]}),data={self.data})"


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
    Represents a parse success as a possibly empty list of result elements.
    """

    def __init__(self, results, context):
        if results is None:
            self._results = []
        elif isinstance(results, Iterable):
            self._results = list(results)
        else:
            self._results = [results]
        self.context = context

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

    def pprint(self, file=None):
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
        Return the result described by parameter matchtype. If "all" returns the whole list of matches.

        Args:
            results: list of results to select from
            matchtype: one of  "first", "shortest", "longest", "all". If there is more than one longest or shortest
               result, the first one of those in the list is returned.

        Returns:
            the filtered match or matches
        """
        if matchtype == None:
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
            matchtype: one of  "first", "shortest", "longest", "all". If there is more than one longest or shortest
               result, the first one of those in the list is returned.

        Returns:
            the filtered match or matches
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
    """

    def __init__(
        self, doc, anns, start=None, end=None, memoize=False, max_recusion=None
    ):
        """
        Initialize a parse context.

        Args:
            doc: the document which should get parsed
            anns: an iterable of annotations to use for the parsing
            start: the starting text offset for the parse
            end: the ending text offset for the parse
            memoize: If memoization should be used (NOT YET IMPLEMENTED)
            max_recusion: the maximum recursion depth for recursive parse rules (NOT YET IMPLEMENTED)
        """
        self._memotable = {}
        self.max_recursion = max_recusion
        self.doc = doc
        self._annset = None    # cache for the annotations as a detached immutable set, if needed
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

    When subclassing, the parse(location, context) method must be overriden!
    """

    def __init__(self, parser_function):
        self.name = None
        self._parser_function = parser_function
        self.name = parser_function.__name__
        functools.update_wrapper(self, parser_function)

    def parse(self, location, context):
        return self._parser_function(location, context)

    def match(self, doc, anns=None, start=None, end=None, location=None):
        """
        Runs the matcher on the given document and the given annotations. Annotations may be empty in which
        case only matching on text makes sense.

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
            Either Success or Failure

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
        return Or(self, other)

    def __rshift__(self, other):
        return Seq(self, other)

    def __and__(self, other):
        return And(self, other)

    def __xor__(self, other):
        """
        Return a parser that succeeds if this or the other parser succeeds and return the union of all results.
        Fails if both parsers fail.

        NOTE: `a ^ b ^ c` is NOT the same as All(a,b,c) as the first will fail if b fails but the second will
        still return `a ^ c`

        Args:
            other:

        Returns:

        """
        return All(self, other)

    def where(self, predicate, take_if=True):
        return Filter(self, predicate, take_if=take_if)

    def repeat(self, min=1, max=1):
        return N(self, min=min, max=max)

    def __mul__(self, n):
        if isinstance(n, int):
            return N(self, min=n, max=n)
        elif isinstance(n, tuple) and len(n) == 2:
            return N(self, min=n[0], max=n[1])
        elif isinstance(n, list) and len(n) == 2:
            return N(self, min=n[0], max=n[1])
        else:
            raise Exception("Not an integer or tuple or list of two integers")

    def _make_constraint_predicate(self, matcher, matchtype, constraint):
        """
        Create predicate that can be used to filter results according to one of the
        annotation-based constraints like .within, .coextensive.

        Args:
            matcher: the annotation matcher
            matchtype: the matchtype for the filter
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

    def _make_notconstraint_predicate(self, matcher, matchtype, constraint):
        """
        Create predicate that can be used to filter results according to one of the
        annotation-based negated constraints like .notwithin, .notcoextensive.

        Args:
            matcher: the annotation matcher
            matchtype: the matchtype for the filter
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

    def within(self, type=None, features=None, features_eq=None, text=None, matchtype="first"):
        """
        Parser that succeeds if there is a success for the current parser that is within any annotation
        that matches the given properties and is different from that annotation.

        Args:
            type:
            features:
            features_eq:
            text:
            matchtype: return matches of all that are within the span according to the given strategy

        Returns:
            Parser modified to only match within a matching annotation
        """
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, matchtype, "covering")
        return Filter(self, pred, matchtype=matchtype)

    def notwithin(self, type=None, features=None, features_eq=None, text=None, matchtype="first"):
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, matchtype, "covering")
        return Filter(self, pred, matchtype=matchtype)

    def coextensive(self, type=None, features=None, features_eq=None, text=None,  matchtype="first"):
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, matchtype, "coextensive")
        return Filter(self, pred, matchtype=matchtype)

    def notcoextensive(self, type=None, features=None, features_eq=None, text=None,  matchtype="first"):
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, matchtype, "coextensive")
        return Filter(self, pred, matchtype=matchtype)

    def overlapping(self, type=None, features=None, features_eq=None, text=None,  matchtype="first"):
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, matchtype, "overlapping")
        return Filter(self, pred, matchtype=matchtype)

    def notoverlapping(self,type=None, features=None, features_eq=None, text=None,  matchtype="first"):
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, matchtype, "overlapping")
        return Filter(self, pred, matchtype=matchtype)

    def covering(self, type=None, features=None, features_eq=None, text=None, matchtype="first"):
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, matchtype, "within")
        return Filter(self, pred, matchtype=matchtype)

    def notcovering(self, type=None, features=None, features_eq=None, text=None,  matchtype="first"):
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, matchtype, "within")
        return Filter(self, pred, matchtype=matchtype)

    def at(self, type=None, features=None, features_eq=None, text=None,  matchtype="first"):
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_constraint_predicate(matcher, matchtype, "start_eq")
        return Filter(self, pred, matchtype=matchtype)

    def noat(self, type=None, features=None, features_eq=None, text=None,  matchtype="first"):
        matcher = AnnMatcher(
            type=type, features=features, features_eq=features_eq, text=text
        )
        pred = self._make_notconstraint_predicate(matcher, matchtype, "start_eq")
        return Filter(self, pred, matchtype=matchtype)

    def before(self, type=None, features=None, features_eq=None, text=None, immediately=False, matchtype="first"):
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
                annstocheck = annset.start_eq(result.span[1])
            else:
                annstocheck = annset.start_ge(result.span[1])
            for anntocheck in annstocheck:
                if matcher(anntocheck, context.doc):
                    if anntocheck in anns:
                        continue
                    return True
            return False
        return Filter(self, _predicate, matchtype=matchtype)

    @support_annotation_or_set
    def notbefore(self,  type=None, features=None, features_eq=None, text=None, immediately=False, matchtype="first"):
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
                annstocheck = annset.start_eq(result.span[1])
            else:
                annstocheck = annset.start_ge(result.span[1])
            matched = False
            for anntocheck in annstocheck:
                if matcher(anntocheck, context.doc):
                    if anntocheck in anns:
                        continue
                    matched = True
            return not matched
        return Filter(self, _predicate, matchtype=matchtype)

    def lookahead(self, parser):
        """
        Return a parser that makes sure the given parser has at least one match before returning success.

        Args:
            parser:

        Returns:

        """
        return Lookahead(self, parser)


class Lookahead(PampacParser):
    def __init__(self, parser, laparser):
        self.parser = parser
        self.laparser = laparser

    def parse(self, location, context):
        if context.parse(location, context).issuccess():
            return self.parser.parse(location, context)
        else:
            return Failure(
                context=context, message="Lookahead failed", location=location
            )


class Filter(PampacParser):
    """
    Select only some of the results returned by a parser success, call the predicate function on each to check.
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
                if self.predicate(r, context=context, location=location) == self.take_if:
                    res.append(r)
            if len(r) == 0:
                return Failure(
                    context=context,
                    location=location,
                    message="No result satisfies predicate",
                )
            else:
                return Success(res)
        else:
            return ret


class Call(PampacParser):
    def __init__(self, parser, func, onfailure=None):
        self.parser = parser
        self.func = func
        self.onfailure = onfailure

    def parse(self, location, context):
        ret = self.parser.parse(location, context)
        if ret.issuccess():
            self.func(ret,
                      context=context,
                      location=location,
                      name=self.parser.name,
                      parser=self.parser.__class__.__name__)
        else:
            if self.onfailure:
                self.onfailure(
                    ret,
                    context=context,
                    location=location,
                    name=self.parser.name,
                    parser=self.parser.__class__.__name__
                )
        return ret


class _AnnBase(PampacParser):
    """
    Common code for both Ann and AnnAt"
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
                return Failure(context=context, location=location, message="No annotation left")
            if ann.start >= location.text_location + min and ann.start <= location.text_location + max:
                return self.parse(location, context)
            else:
                return Failure(context=context, location=location, message="Next ann not withing gap")
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
                    return Failure(context=context, location=location, message="No annotation left")
                if ann.start >= location.text_location + min and ann.start <= location.text_location + max:
                    return self.parse(location, context)
                if ann.ann.start > location.text_location + max:
                    return Failure(context=context, location=location, message="No annotation found withing gap")
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
                parser=self,
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
                        location=matchlocation,
                        ann=next_ann,
                        name=self.name,
                        parser=self.__class__.__name__,
                    )
                # update location
                location = context.inc_location(location, by_index=1)
                result = Result(
                    data=data, location=location, span=(next_ann.start, next_ann.end)
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
                parser=self,
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
        """
        Try to match the given annotation at the current context location. If we succeed,

        Args:
            location: the location of where to parse next
            context: parser context

        Returns:
            Success or Failure
        """
        if self.useoffset:
            location = context.update_location_byoffset(location)
        next_ann = context.get_ann(location)
        if not next_ann:
            return Failure(
                context=context,
                parser=self,
                location=location,
                message="No annotation left",
            )
        # try to match it
        if self._matcher(next_ann, doc=context.doc):
            newlocation = context.inc_location(location, by_index=1)
            if self.name is not None:
                data = dict(
                    location=location,
                    ann=next_ann,
                    name=self.name,
                    parser=self.__class__.__name__,
                )
            else:
                data = None
            span = (next_ann.start, next_ann.end)
            return Success(Result(data=data, span=span, location=newlocation), context)
        else:
            return Failure(location=location, context=context, parser=self)


class Find(PampacParser):
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
        location = context.update_location_byindex(location)
        txt = context.doc.text[location.text_location :]
        if isinstance(self.text, CLASS_RE_PATTERN) or isinstance(
            self.text, CLASS_REGEX_PATTERN
        ):
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
                        parser=self.__class__.__name__,
                    )
                else:
                    data = None
                span = (location.text_location, location.text_location + len(m.group()))
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
                        location=location,
                        text=self.text,
                        name=self.name,
                        parser=self.__class__.__name__,
                    )
                else:
                    data = None
                newlocation = context.inc_location(location, by_offset=len(self.text))
                span = (location.text_location, location.text_location + len(self.text))
                return Success(
                    Result(data=data, location=newlocation, span=span), context
                )
            else:
                return Failure(context=context)


class Or(PampacParser):
    """
    Create a parser that accepts the first of all the parsers specified.
    """

    def __init__(self, *parsers, matchtype="all"):
        """
        Creates a parser that tries each of the given parsers in order and uses the first
        one that finds a successful match only.

        Args:
            *parsers: two or more parsers to each try in sequence
            matchtype: which of the results from the successful parser to return.
        """
        assert len(parsers) > 0
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
    def __init__(self, *parsers):
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
    def __init__(self, *parsers):
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
    A parser that represents a sequence of matching parsers. This parser will combine
    """

    def __init__(self, *parsers, matchtype="first", select="first"):
        """

        Args:
            *parsers: one or more parsers
            matchtype: (default "first") one of "first", "longest", "shortest", "all": which match to return.
              Note that even if a matchtype for a single match is specified, the parser may still need to
              generate an exponential number of combinations for all the results to select from.
            select: (default "first") one of "first", "longest", "shortest", "all": which match to choose from each
              of the parsers. Only if "all" is used will more than one result be generated.
        """
        assert len(parsers) > 0
        self.parsers = parsers
        if matchtype is None:
            matchtype = "first"
        assert matchtype in ["first", "longest", "shortest", "all"]
        self.select = select
        self.matchtype = matchtype

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
                        start = result.span[0]
                    end = result.span[1]
                else:
                    return Failure(
                        context=context, location=location, message="Mismatch in Seq"
                    )
            return Success(
                Result(data=datas, location=location, span=(start, end)), context
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
                        span = (location.text_location, res.location.text_location)
                        newresult = Result(datas, location=loc, span=span)
                        if lvl == len(self.parsers) - 1:
                            yield newresult
                        else:
                            yield from depthfirst(lvl + 1, newresult)

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
                    elif result.span[1] > best.span[1]:
                        best = result
                elif self.matchtype == "shortest":
                    if best is None:
                        best = result
                    elif result.span[1] < best.span[1]:
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
    A parser that represents a sequence of k to l matching parsers, greedy.
    """

    def __init__(
        self, parser, min=1, max=1, matchtype="first", select="first", until=None
    ):
        """
        Return a parser that matches min to max matches of parser in sequence. If until is specified, that
        parser is tried to match before each iteration and as soon as it matched, the parser succeeds.
        If after ming to max matches of the parser, until does not match, the parser fails.

        Args:
            parser:
            min:
            max:
            matchtype:
            until:
        """
        self.parser = parser
        self.min = min
        self.max = max
        self.matchtype = matchtype
        self.until = until
        self.select = select

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
                        end = res.span[1]
                        return Success(
                            Result(datas, location=loc, span=(start, end)), context
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
                        return Success(
                            Result(data=datas, location=location, span=(start, end)),
                            context,
                        )
                else:
                    result = ret.result(self.select)
                    if first:
                        first = False
                        start = result.span[0]
                    end = result.span[1]
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
                    end = res.span[1]
                    for d in data:
                        datas.append(d)
                    return Success(
                        Result(datas, location=loc, span=(start, end)), context
                    )
                else:
                    return Failure(
                        context=context,
                        location=location,
                        message="Until parser not successful",
                    )
            return Success(
                Result(data=datas, location=location, span=(start, end)), context
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
                            end = res.span[1]
                            yield Result(data, location=loc, span=(start, end))
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
                        span = (location.text_location, res.location.text_location)
                        newresult = Result(datas, location=loc, span=span)
                        yield from depthfirst(lvl + 1, newresult)
                else:
                    if lvl <= self.min:
                        return
                    else:
                        # we already have at least min matches: if we have no until, we can yield the result
                        if not self.until:
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
                    elif result.span[1] > best.span[1]:
                        best = result
                elif self.matchtype == "shortest":
                    if best is None:
                        best = result
                    elif result.span[1] < best.span[1]:
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
    Basically just a different way to write "parser(pattern).call(func)" plus set additional options for the
    rule runner (priority).
    """

    def __init__(self, parser, func, priority=0):
        self.parser = parser
        self.func = func
        self.priority = priority

    def parse(self, location, context):
        """
        For a rule, we return the parse result and the result of the code running if we have success.

        Args:
            location: the document location
            context: the parsing context

        Returns:
            tuple of parse result and if success, function return value, otherwise None

        """
        res = self.parser.parse(location, context)
        if res.success():
            if self.func:
                val = self.func(res)
            else:
                val = None
            return res, val
        else:
            return res, None

class PampacRunner:
    """
    A runner for executing rules in some specific way.

    E.g. PampacRunner(strategy="something", ...).rules(r1,r2,r3). or just
    PampacRunner(strategy="something", ...)(r1,r2,r3)

    """
    def __init__(self, *rules, skip="longest", select="first", debug=False):
        assert len(rules) > 0
        self.rules = rules
        self.skip = skip
        self.select = select
        self.debug = debug

    def skip(self, val):
        """
        Different way to set the skip parameter.

        Args:
            val:

        Returns:

        """
        self.skip = val

    def select(self, val):
        """
        Different way to set the select parameter.

        Args:
            val:

        Returns:

        """
        self.select = val

    def run(self, doc, annotations, start=None, end=None):
        """
        Run the rules from location start to location end (default: full document), using the annotation set or list.

        Args:
            doc:
            annotations:
            start:
            end:

        Returns:
            a flattened list of all non-None results of Rule functions that fired on the document.
        """
        pass



    __call__ = run
