"""
Module for PAMPAC data structures.

This defines classes for representing the parser location (Location), a parsing result (Result),
and successful and unsuccessful parses (Success, Failure).
"""
from typing import Union
from collections.abc import Iterable, Sized
from gatenlp import AnnotationSet, Annotation


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


class Result(Iterable, Sized):
    """
    Represents an individual parser result. A successful parse can have any number of parser results which
    are alternate ways of how the parser can match the document. Each result can have an arbitrary number of
    "matches" (named spans where some part of the pattern fits the document).
    A result is an iterable of matches.
    """

    def __init__(self, matches=None, location=None, span=None):
        """
        Create a parser result.

        Args:
            matches: the matching info  associated with the result, this can be a single item or a list of items.
            location: the location where the result was matched, i.e. the location *before* matching was done.
            span: the span representing the start and end text offset for the match
        """
        assert location is not None
        assert span is not None
        if matches is not None:
            if isinstance(matches, dict):
                self.matches = [matches]
            elif isinstance(matches, Iterable):
                self.matches = list(matches)
            else:
                self.matches = [matches]
        else:
            self.matches = []
        self.location = location
        self.span = span

    def anns4matches(self):
        """
        Yields all the annotations, if any, in the results matches.
        """
        for mtch_ in self.matches:
            tmp = mtch_.get("ann")
            if tmp:
                yield tmp

    def matches4name(self, name):
        """
        Return a list of match info dictionaries with the given name.
        """
        return [m for m in self.matches if m.get("name") == name]

    def __str__(self):
        return f"Result(loc={self.location},span=Span({self.span.start},{self.span.end}),nmatches={len(self.matches)})"

    def __repr__(self):
        return f"Result(loc={self.location},span=Span({self.span.start},{self.span.end}),matches={self.matches})"

    def __iter__(self):
        if self.matches is not None:
            return iter(self.matches)
        else:
            return iter([])

    def __len__(self):
        if self.matches is not None:
            return len(self.matches)
        else:
            return 0


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
    of matching info for named patterns that match.
    A result represents a fitting pattern at the top/outermost level of a parser.
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
        elif isinstance(results, Result):   # now that the Result itself is an iterable, need to check first!
            self._results = [results]
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

    def pprint(self, file=None):  # pragma: no cover
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
            for jdx, mtch_ in enumerate(res.matches):
                if file:
                    print(f"  {jdx}: {mtch_}", file)
                else:
                    print(f"  {jdx}: {mtch_}", file)

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
    Context contains information and refers to information for carrying out the parse.

    A context contains a reference to the document being parsed, the list of annotations to use,
    the start and end text offsets the parsing should be restricted to, the output annotation set
    to use, the maximum recursion depth and a structure for memoization.

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
            # memoize=False,
            # max_recusion=None,
        ):
        """
        Initialize a parse context.

        Args:
            doc: the document which should get parsed
            anns: an iterable of annotations to use for the parsing. The annotations are used in the order they
                occur in the iterator (for a set, this is the default order by start offset and annotation id).
                If the order is different from the default order, the result may be unexpected or matching may not
                work depending on the exact patterns used.
            start: the starting text offset for the parse
            end: the ending text offset for the parse
            outset: an annotation set for where to add any new annotations in an action
        """
        #             max_recusion: the maximum recursion depth for recursive parse rules (NOT YET IMPLEMENTED)
        # self._memotable = {}
        # self.max_recursion = max_recusion
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
        # self.memoize = memoize

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

    def get_ann(self, location) -> Union[Annotation, None]:
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
        # print(f"DEBUG Trying to find next idx for curlocation={location} and curidx={idx}, offset={offset}")
        if next_ann:
            idx += 1
        while True:
            if idx >= len(self.anns):
                return len(self.anns)
            ann = self.anns[idx]
            # print(f"DEBUG Checking ann={ann}")
            if ann.start >= offset:
                return idx
            idx += 1

    def inc_location(self, location, by_offset=None, by_index=None, to_offset=None):
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
            to_offset: if given, the by_ arguments are ignored and instead the offset is set to the given
                offset with the annotation index set to the next annotation at or after that offset

        Returns:
            new location
        """
        newloc = Location(
            text_location=location.text_location, ann_location=location.ann_location
        )
        if to_offset is not None:
            assert to_offset < self.end
            assert to_offset >= self.start
            newloc.text_location = to_offset
            newloc.ann_location = self.nextidx4offset(
                location, newloc.text_location
            )
        elif by_index is not None:
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
            # print(f"DEBUG Updating by text offset: {by_offset}, current loc is {newloc.text_location}")
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
            # we already are beyond the last annotation so we set the text offset to beyond the text
            return Location(len(self.doc.text), location.ann_location)
        else:
            # set the text location to the end of the current annotation
            return Location(
                self.anns[location.ann_location].end, location.ann_location
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