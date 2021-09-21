"""
Module for PAMPAC (Pattern Matching wit PArser Combinators) parsers.

This module allows to create parsers that can match
patterns in annotations and text and carry out actions if a match occurs.

NOTE: this implementation has been inspired by https://github.com/google/compynator
"""
# pylint: disable=C0302,R0911,R0912,R0915
from abc import ABC, abstractmethod
import functools
from gatenlp.pam.matcher import AnnMatcher, CLASS_REGEX_PATTERN, CLASS_RE_PATTERN
from gatenlp.pam.pampac.data import Location, Context, Result, Success, Failure
from gatenlp.utils import support_annotation_or_set
from gatenlp import Span

__pdoc__ = {
    "PampacParser.__or__": True,
    "PampacParser.__xor__": True,
    "PampacParser.__rshift__": True,
    "PampacParser.__and__": True,
    "PampacParser.__mul__": True,
    "_AnnBase": True,
}


class PampacParser(ABC):
    """
    A Pampac parser, something that takes a context and returns a result.
    This can be used to decorate a function that should be used as the parser,
    or for subclassing specific parsers.

    When subclassing, the method `parse(location, context)`  must be overriden!

    All parsers are callables where the `__call__` method has the same signature as the
    `match` method. So `SomeParser(...)(doc, anns)` is the same as `SomeParser(...).match(doc, anns)`

    """

    @abstractmethod
    def parse(self, location, context):
        """
        The parsing method that needs to get overridden by each parser implementation.

        Args:
            location: current location for where to continue parsing
            context:  the context instance

        Returns:
            success or failure instance

        """

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

    def repeat(self, min=1, max=1):  # pylint: disable=W0622
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

    def __mul__(self, n):  # pylint: disable=C0103
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

    def _make_constraint_predicate(self, matcher, constraint, annset=None):
        """
        Create predicate that can be used to filter results according to one of the
        annotation-based constraints like .within, .coextensive.

        Args:
            matcher: the annotation matcher
            constraint: the constraint to use on the annotation set
            annset: if not None, use that set instead of the one from the context

        Returns:
            predicate function

        """
        def _predicate(result, context=None, **_kwargs):
            anns = set()
            for mtch_ in result.matches:
                ann = mtch_.get("ann")
                if ann:
                    anns.add(ann)
            if annset is None:
                useset = context.annset
            else:
                useset = annset
            tocall = getattr(useset, constraint)
            annstocheck = tocall(result.span)
            for anntocheck in annstocheck:
                if matcher(anntocheck, context.doc):
                    if anntocheck in anns:
                        continue
                    return True
            return False

        return _predicate

    def _make_notconstraint_predicate(self, matcher, constraint, annset=None):
        """
        Create predicate that can be used to filter results according to one of the
        annotation-based negated constraints like .notwithin, .notcoextensive.

        Args:
            matcher: the annotation matcher
            constraint: the constraint to use on the annotation set
            annset: if not None, use that set instead of the one from the context

        Returns:
            predicate function

        """
        def _predicate(result, context=None, **_kwargs):
            anns = set()
            for mtch_ in result.matches:
                ann = mtch_.get("ann")
                if ann:
                    anns.add(ann)
            if annset is None:
                useset = context.annset
            else:
                useset = annset
            tocall = getattr(useset, constraint)
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
            self, type=None,
            annset=None,
            features=None,
            features_eq=None, text=None, matchtype="first"
    ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is within any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_constraint_predicate(matcher, "covering", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def notwithin(
            self, type=None, annset=None, features=None, features_eq=None, text=None, matchtype="first"
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is not within any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_notconstraint_predicate(matcher, "covering", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def coextensive(
            self, type=None, annset=None, features=None, features_eq=None, text=None, matchtype="first"
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is coextensive with
        any annotation that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_constraint_predicate(matcher, "coextensive", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def notcoextensive(
            self, type=None, annset=None, features=None, features_eq=None, text=None, matchtype="first"
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is not coextensive
        with any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_notconstraint_predicate(matcher, "coextensive", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def overlapping(
            self, type=None, annset=None, features=None, features_eq=None, text=None, matchtype="first"
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is overlapping with
        any annotation that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_constraint_predicate(matcher, "overlapping", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def notoverlapping(
            self, type=None, annset=None, features=None, features_eq=None, text=None, matchtype="first"
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is not overlapping
        within any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_notconstraint_predicate(matcher, "overlapping", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def covering(
            self, type=None, annset=None, features=None, features_eq=None, text=None, matchtype="first"
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is covering any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_constraint_predicate(matcher, "within", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def notcovering(
            self, type=None, annset=None, features=None, features_eq=None, text=None, matchtype="first"
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is not covering
        any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_notconstraint_predicate(matcher, "within", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def at(
            self, type=None, annset=None, features=None, features_eq=None, text=None, matchtype="first"
        ):  # pylint: disable=W0622,C0103
        """
        Parser that succeeds if there is a success for the current parser that is starting
        at the same offset as an annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_constraint_predicate(matcher, "startingat", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def notat(
            self, type=None, annset=None, features=None, features_eq=None, text=None, matchtype="first"
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is not starting
        with any annotation
        that matches the given properties.

        NOTE: all the annotations matched in any of the results of this parser are excluded from
        the candidates for checking this constraint!

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
        pred = self._make_notconstraint_predicate(matcher, "startingat", annset=annset)
        return Filter(self, pred, matchtype=matchtype)

    def before(
            self,
            type=None,
            annset=None,
            features=None,
            features_eq=None,
            text=None,
            immediately=False,
            matchtype="first",
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is before any annotation
        that matches the given properties.

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
            anns = set(result.anns4matches())
            if annset is None:
                useset = context.annset
            else:
                useset = annset
            if immediately:
                annstocheck = useset.startingat(result.span.end)
            else:
                annstocheck = useset.startin_ge(result.span.end)
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
            annset=None,
            features=None,
            features_eq=None,
            text=None,
            immediately=False,
            matchtype="first",
        ):  # pylint: disable=W0622
        """
        Parser that succeeds if there is a success for the current parser that is not before any annotation
        that matches the given properties.

        Args:
            type: as for AnnMatcher
            annset: if not None, check for an annotation in that set instead of the default set used
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
            anns = set(result.anns4matches())
            if annset is None:
                useset = context.annset
            else:
                useset = annset
            if immediately:
                annstocheck = useset.startingat(result.span.end)
            else:
                annstocheck = useset.start_ge(result.span.end)
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


class Function(PampacParser):
    """
    Parser that wraps a function.
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
                for mtch_ in res:
                    newlocation = mtch_.location
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
            predicate: the function to call for each result of the parser success. Should have signature
                result, context=, location=
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
            for res_ in ret:
                if (
                        self.predicate(res_, context=context, location=location)
                        == self.take_if
                ):
                    res.append(res_)
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

    def gap(self, min=0, max=0):  # pylint: disable=W0622
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

        return Function(parser_function=_parse)

    def findgap(self, min=0, max=0):  # pylint: disable=W0622
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
                idx += 1

        return Function(parser_function=_parse)


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
        ):  # pylint: disable=W0622
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
                    matches = None
                else:
                    matches = dict(
                        span=Span(next_ann.start, next_ann.end),
                        location=matchlocation,
                        ann=next_ann,
                        name=self.name,
                    )
                # update location
                result_location = context.inc_location(location, by_index=1)
                result = Result(matches=matches, location=result_location, span=Span(next_ann.start, next_ann.end))
                if self.matchtype == "first":
                    return Success(result, context)
                results.append(result)
                # have we reached the last annotation?
                if context.at_endofanns(location):
                    break
                # point to the next annotation
                location.ann_location += 1
                next_ann = context.get_ann(location)
                if not next_ann or next_ann.start != start:
                    break
            else:
                if context.at_endofanns(location):
                    break
                # point to the next annotation
                location.ann_location += 1
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
        ):  # pylint: disable=W0622
        """

        Args:
            type: (default: None): type to match, string, regexp or predicate function
            features: (default: None): features to match, dictionary where each value is value, regexp or predicate function
               Annotation can contain additional features.
            features_eq: (default: None): features to match, annotation must not contain additional features
            text: (default: None): document text to match, string or regexp
            name: (default: None): if set to a non-empty string, saves the match info under this name
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
                matches = dict(
                    span=Span(next_ann),
                    location=location,
                    ann=next_ann,
                    name=self.name,
                )
            else:
                matches = None
            span = Span(next_ann.start, next_ann.end)
            return Success(Result(matches=matches, location=newlocation, span=span), context)
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
            name:  if not None saves the match information under that name
            matchcase: if text is actual text, whether the match should be case sensitive or not
        """
        self.text = text
        if isinstance(self.text, str) and not matchcase:
            self.text = self.text.upper()
        self.name = name
        self.matchcase = matchcase

    def parse(self, location, context):
        # TODO: why did we update by index here before trying to match? Are there edge cases where this
        #   is needed? In general it is bad because it will set the text offset to the end of the NEXT
        #   annotation which we do not want. So maybe there are cases when either the current text offset
        #   does not coincide with the current annotation index or where the annotation index was not
        #   updated.
        # print(f" DEBUG BEFORE: {location}")
        # location = context.update_location_byindex(location)
        # print(f"DEBUG AFTER: {location}")
        txt = context.doc.text[location.text_location:]
        if isinstance(self.text, (CLASS_RE_PATTERN, CLASS_REGEX_PATTERN)):
            mtch_ = self.text.match(txt)
            if mtch_:
                lengrp = len(mtch_.group())
                newlocation = context.inc_location(location, by_offset=lengrp)
                if self.name:
                    matches = dict(
                        location=location,
                        span=Span(
                            location.text_location,
                            location.text_location + len(mtch_.group()),
                        ),
                        text=mtch_.group(),
                        groups=mtch_.groups(),
                        name=self.name,
                    )
                else:
                    matches = None
                span = Span(
                    location.text_location, location.text_location + len(mtch_.group())
                )
                return Success(
                    Result(matches=matches, location=newlocation, span=span), context
                )
            else:
                return Failure(context=context)
        else:
            if not self.matchcase:
                txt = txt.upper()
            if txt.startswith(self.text):
                if self.name:
                    matches = dict(
                        span=Span(
                            location.text_location,
                            location.text_location + len(self.text),
                        ),
                        location=location,
                        text=self.text,
                        name=self.name,
                    )
                else:
                    matches = None
                newlocation = context.inc_location(location, by_offset=len(self.text))
                span = Span(
                    location.text_location, location.text_location + len(self.text)
                )
                return Success(
                    Result(matches=matches, location=newlocation, span=span), context
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
        for parser_ in self.parsers:
            ret = parser_.parse(location, context)
            if ret.issuccess():
                if self.matchtype == "all":
                    return ret
                result = ret.result(self.matchtype)
                newloc = result.location
                return Success(
                    Result(result.matches, location=newloc, span=result.span), context
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
        for parser_ in self.parsers:
            ret = parser_.parse(location, context)
            if ret.issuccess():
                for res_ in ret:
                    results.append(res_)
            else:
                return Failure(
                    context=context,
                    location=location,
                    message="Not all parsers succeed",
                )
        return Success(results, context=context)


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
        for parser_ in self.parsers:
            ret = parser_.parse(location, context)
            if ret.issuccess():
                for res_ in ret:
                    results.append(res_)
        if len(results) > 0:
            return Success(results, context=context)
        else:
            return Failure(
                context=context,
                location=location,
                message="None of the parsers succeeded",
            )


class Seq(PampacParser):
    """
    A parser that represents a sequence of matching parsers. Each result of this parser combines
    all the match information from the sequence element parsers. For matchtype all and select all, all paths
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
            name: if not None, a separate matching info element is added to the result with that name and
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
            allmatches = []
            first = True
            start = None
            end = None
            for parser in self.parsers:
                ret = parser.parse(location, context)
                if ret.issuccess():
                    result = ret.result(self.select)
                    for mtch in result.matches:
                        allmatches.append(mtch)
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
                allmatches.append(
                    dict(span=Span(start, end), name=self.name, location=location)
                )
            return Success(
                Result(matches=allmatches, location=location, span=Span(start, end)), context
            )
        else:
            # This does a depth-first enumeration of all matches: each successive parser gets tried
            # for each result of the previous one.

            def depthfirst(lvl, result, start):
                parser = self.parsers[lvl]
                ret = parser.parse(result.location, context)
                if ret.issuccess():
                    for res in ret:
                        if start == -1:
                            start = res.span.start
                        tmpmatches = result.matches.copy()
                        for dmtch in res.matches:
                            tmpmatches.append(dmtch)
                        loc = res.location
                        span = Span(start, res.span.end)
                        if lvl == len(self.parsers) - 1:
                            if self.name:
                                tmpmatches.append(
                                    dict(
                                        span=span,
                                        location=loc,
                                        name=self.name,
                                    )
                                )
                            newresult = Result(tmpmatches, location=loc, span=span)
                            yield newresult
                        else:
                            newresult = Result(tmpmatches, location=loc, span=span)
                            yield from depthfirst(lvl + 1, newresult, start)

            gen = depthfirst(0, Result(matches=[], location=location, span=Span(0, 0)), -1)
            all_ = []
            best = None
            for idx, result in enumerate(gen):
                if self.matchtype == "first" and idx == 0:
                    return Success(result, context)
                if self.matchtype == "all":
                    all_.append(result)
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
                if len(all_) > 0:
                    return Success(all_, context)
                else:
                    return Failure(context=context, location=location)
            else:
                if best is not None:
                    return Success(best, context)
                else:
                    return Failure(context=context, location=location)


class N(PampacParser):  # pylint: disable=C0103
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
        ):  # pylint: disable=W0622
        """
        Return a parser that matches min to max matches of parser in sequence. If until is specified, that
        parser is tried to match before each iteration and as soon as it matched, the parser succeeds.
        If after ming to max matches of the parser, until does not match, the parser fails.

        Args:
            parser: the parser that should match min to max times
            min: minimum number of times to match for a success
            max: maximum number of times to match for a success
            matchtype: which results to include in a successful match, one of "first", "longest", "shortest", "all"
            select: (default "first") one of "first", "longest", "shortest", "all": which match to choose from each
                of the parsers. Only if "all" is used will more than one result be generated.
            until: parser that terminates the repetition
            name: if not None, adds an additional match info element to the result which contains the
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
        # print(f"!!!!!!!!!!!DEBUG: trying to match at {location}")
        start = location.text_location
        end = start
        if self.select != "all":
            allmatches = []
            i = 0
            first = True
            # location is the location where we try to match
            while True:
                if self.until and i >= self.min:
                    ret = self.until.parse(location, context)
                    if ret.issuccess():
                        res = ret.result(self.select)
                        for matches_ in res.matches:
                            allmatches.append(matches_)
                        loc = res.location
                        end = res.span.end
                        if self.name:
                            allmatches.append(
                                dict(
                                    span=Span(start, end), location=loc, name=self.name
                                )
                            )
                        return Success(
                            Result(allmatches, location=loc, span=Span(start, end)), context
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
                            allmatches.append(
                                dict(
                                    span=Span(start, end),
                                    location=location,
                                    name=self.name,
                                )
                            )
                        return Success(
                            Result(matches=allmatches, location=location, span=Span(start, end)),
                            context,
                        )
                else:
                    result = ret.result(self.select)
                    if first:
                        first = False
                        start = result.span.start
                    end = result.span.end
                    for matches_ in result.matches:
                        allmatches.append(matches_)
                    location = result.location
                    i += 1
                    if i == self.max:
                        break
            if self.until:
                ret = self.until.parse(location, context)
                if ret.issuccess():
                    res = ret.result(self.select)
                    loc = res.location
                    end = res.span.end
                    for matches_ in res.matches:
                        allmatches.append(matches_)
                    if self.name:
                        allmatches.append(
                            dict(span=Span(start, end), location=loc, name=self.name)
                        )
                    return Success(
                        Result(allmatches, location=loc, span=Span(start, end)), context
                    )
                else:
                    return Failure(
                        context=context,
                        location=location,
                        message="Until parser not successful",
                    )
            if self.name:
                allmatches.append(
                    dict(span=Span(start, end), location=location, name=self.name)
                )
            return Success(
                Result(matches=allmatches, location=location, span=Span(start, end)), context
            )
        else:  # select="all"
            # This does a depth-first enumeration of all matches: each successive parser gets tried
            # for each result of the previous one.
            # TODO: figure out how to properly add named matches!
            def depthfirst(lvl, result, start):
                # if we already have min matches and we can terminate early, do it
                if self.until and lvl >= self.min:
                    ret = self.until.parse(result.location, context)
                    if ret.issuccess():
                        for res in ret:
                            tmpmatches = result.matches.copy()
                            for mtmp in res.matches:
                                tmpmatches.append(mtmp)
                            loc = res.location
                            end = res.span.end
                            if self.name:
                                tmpmatches.append(
                                    dict(
                                        span=Span(start, end),
                                        location=location,
                                        name=self.name,
                                    )
                                )
                            tmpres = Result(tmpmatches, location=loc, span=Span(start, end))
                            # print(f"DEBUG: YIELD4 {tmpres}")
                            yield tmpres
                            return
                # if we got here after the max number of matches, and self.until is set, then
                # the parse we did above did not succeed, so we end without a result
                if self.until and lvl > self.max:
                    return
                # if we got here after the max number of matches and self.util is not set, we
                # can yield the current result as we found max matches
                if lvl >= self.max:
                    # print(f"DEBUG: YIELD2 {result}")
                    yield result
                    return
                # lvl is still smaller than max, so we try to match more
                ret = self.parser.parse(result.location, context)
                # print(f"DEBUG: got success={ret}, start={start}")
                if ret.issuccess():
                    # for each of the results, try to continue matching
                    for res in ret:
                        # print(f"DEBUG: processing result {res}")
                        tmpmatches = result.matches.copy()
                        for matches_ in res.matches:
                            tmpmatches.append(matches_)
                        loc = res.location
                        if start == -1:
                            start = res.span.start
                            # print(f"!!!!!!!!! DEBUG SETTING Start to {start}")
                        span = Span(start, res.span.end)
                        # WAS: span = Span(location.text_location, res.location.text_location)
                        newresult = Result(tmpmatches, location=loc, span=span)
                        # print(f"DEBUG: YIELD FROM {newresult}")
                        yield from depthfirst(lvl + 1, newresult, start)
                else:  # if ret.issuccess()
                    if lvl < self.min:
                        return
                    else:
                        # we already have at least min matches: if we have no until, we can yield the result
                        if not self.until:
                            tmpmatches = result.matches
                            end = result.span.end
                            if self.name:
                                tmpmatches.append(
                                    dict(
                                        span=Span(start, end),
                                        location=result.location,
                                        name=self.name,
                                    )
                                )
                            # print(f"DEBUG: YIELD1 {result}")
                            yield result
                        else:
                            # if we have until, then the until above did not match so neither the normal parser
                            # nor the until did match so we do not have a success
                            return

            gen = depthfirst(0, Result(matches=[], location=location, span=Span(-1, -1)), -1)
            all_ = []
            best = None
            for idx, result in enumerate(gen):
                # if we get a result, and we have a name, add it to the list of named matches
                if self.name:
                    result.matches.append(
                        dict(span=Span(result.span), location=result.location, name=self.name)
                    )
                # print(f"DEBUG: GENERATED RESULT {result}")
                if self.matchtype == "first" and idx == 0:
                    return Success(result, context)
                if self.matchtype == "all":
                    # print(f"DEBUG: APPENDING")
                    all_.append(result)
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
                if len(all_) > 0:
                    tmpret = Success(all_, context)
                    # print(f"DEBUG RETURNING OVERAL OF LENGTH {len(all_)}: {tmpret}")
                    return tmpret
                else:
                    return Failure(context=context, location=location)
            else:
                if best is not None:
                    return Success(best, context)
                else:
                    return Failure(context=context, location=location)
