"""
Module for Annotation class which represents information about a span of text in  a document.
"""
import copy as lib_copy
from functools import total_ordering
from gatenlp.features import Features
from gatenlp.offsetmapper import OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
from gatenlp.utils import support_annotation_or_set, allowspan
from gatenlp.span import Span


@total_ordering
class Annotation:   # pylint: disable=R0904
    """
    An annotation represents information about a span of text. It contains the start and end
    offsets of the span, an "annotation type" and an arbitrary number of features.

    In addition it contains an id which has no meaning for the annotation itself but is
    used to uniquely identify an annotation within the set it is contained in.

    All fields except the features are immutable, once the annotation has been created
    only the features can be changed.
    """

    @allowspan
    def __init__(
            self, start: int, end: int, anntype: str, features=None, annid: int = 0
        ):
        """
        This constructor creates a new annotation instance. Once an annotation has been created,
        the start, end, type and id fields cannot be changed.

        NOTE: this should almost never be done directly
        and instead the method AnnotationSet.add should be used.

        Args:
            start: start offset of the annotation
            end: end offset of the annotation
            anntype: annotation type
            features: an initial collection of features, None for no features.
            annid: the id of the annotation
        """
        if end < start:
            raise Exception(
                f"Cannot create annotation start={start}, end={end}, type={anntype}, "
                "id={annid}, features={features}: start > end"
            )
        if not isinstance(annid, int):
            raise Exception(
                f"Cannot create annotation start={start}, end={end}, type={anntype}, "
                "id={annid}, features={features}: annid is not an int"
            )
        if isinstance(features, int):
            raise Exception(
                f"Cannot create annotation start={start}, end={end}, type={anntype}, "
                "id={annid}, features={features}: features must not be an int, mixed up with annid?"
            )
        self._owner_set = None
        self._features = Features(features, _change_logger=self._log_feature_change)
        self._type = anntype
        self._start = start
        self._end = end
        self._id = annid

    @property
    def type(self) -> str:
        """
        Returns the annotation type.
        """
        return self._type

    @property
    def start(self) -> int:
        """
        Returns the start offset.
        """
        return self._start

    @property
    def end(self):
        """
        Returns the end offset.
        """
        return self._end

    @property
    def features(self):
        """
        Returns the features for the annotation.
        """
        return self._features

    @property
    def id(self):  # pylint: disable=C0103
        """
        Returns the annotation id.
        """
        return self._id

    @property
    def span(self) -> Span:
        """
        Returns a tuple with the start and end offset of the annotation.
        """
        return Span(self._start, self._end)

    def _changelog(self):
        if self._owner_set is not None:
            return self._owner_set.changelog
        return None

    # TODO: for now at least, make sure only simple JSON serialisable things are used! We do NOT
    # allow any user specific types in order to make sure what we create is interchangeable
    # with GATE.
    # In addition we do NOT allow None features.
    # So a feature name always has to be a string (not None), the value has to be anything
    # that is json
    # serialisable (except None keys for maps).
    # For performance reasons we check the feature name but not the value (maybe make checking
    # optional
    # on by default but still optional?)
    def _log_feature_change(
            self, command: str, feature: str = None, value=None
        ) -> None:
        """

        Args:
          command: str:
          feature: str:  (Default value = None)
          value:  (Default value = None)

        Returns:

        """
        if self._changelog() is None:
            return
        command = "ann-" + command
        change = {
            "command": command,
            "type": "annotation",
            "set": self._owner_set.name,
            "id": self.id,
        }
        if feature is not None:
            change["feature"] = feature
        if value is not None:
            change["value"] = value
        self._changelog().append(change)

    def equal(self, other):
        """
        Compare the content of this annotation with other. This returns True if all public attributes
        of the annotations excluding the annotation id (which is ignored) are equal.

        Args:
            other: another object
        """
        return isinstance(other, Annotation) and \
               self.start == other.start and \
               self.end == other.end and \
               self.features == other.features

    def same(self, other):
        """
        Compare the content of this annotation with other. This returns True if all public attributes
        of the annotations including the annotation id are equal.

        Args:
            other: another object
        """
        return isinstance(other, Annotation) and \
               self.id == other.id and \
               self.start == other.start and \
               self.end == other.end and \
               self.features == other.features

    def __lt__(self, other) -> bool:
        """
        Comparison for sorting: this sorts by increasing start offset,
        then increasing annotation id.
        Since annotation ids within a set are unique, this guarantees a unique order of
        annotations that come from an annotation set. For other collections of annotations,
        the order between those with same start offset and same id is undefined.

        IMPORTANT: this is not consistent with our definition of equality and meant for
        easy sorting of annotations from a single set only! Equality is based on the actual
        content of all the fields in an annotation, including the id, while the less than
        relation is only based on start offset and id. It is therefore possible for two
        annotations A1, A2 that A not < B, B not < A and A != B.

        Note: this is defined to match the default order of the default iterator of an
        AnnotationSet. The default order of Span is different, so ordering sorting annotations
        directly and sorting them by their Span can result in different orderings.

        Note: for now the other object has to be an instance of Annotation, duck typing is
        not supported!
        """
        if not isinstance(other, Annotation):
            raise Exception("Cannot compare to non-Annotation")
        if self.start < other.start:
            return True
        elif self.start > other.start:
            return False
        else:
            return self.id < other.id

    def __repr__(self) -> str:
        """
        String representation of the annotation.
        """
        return "Annotation({},{},{},features={},id={})".format(
            self.start, self.end, self.type, self._features, self.id
        )

    @property
    def length(self) -> int:
        """
        Returns the length of the annotation: this is the length of the offset span.
        Since the end offset is one after the last
        element, we return end-start. Note: this is deliberately not implemented as len(ann), as
        len(annset) returns the number of annotations in the set but annset.length()
        also returns the
        span length of the annotation set, so the method name for this is identical between
        annotations
        and annotation sets.
        """
        return self.end - self.start

    @support_annotation_or_set
    def isoverlapping(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is overlapping with the given span, annotation or
        annotation set.

        Note: this can be called with an Annotation or AnnotationSet instead of `start` and `end`
          (see gatenlp._utils.support_annotation_or_set)

        Args:
          start: start offset of the span
          end: end offset of the span

        Returns:
          `True` if overlapping, `False` otherwise

        """
        if start == end:
            return self.iscovering(start)
        else:
            return self.iscovering(start) or self.iscovering(end - 1)

    @support_annotation_or_set
    def isleftoverlapping(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is overlapping with the given span, annotation or
        annotation set on the left, i.e. the last character is inside the span and the
        first character is before the span.

        Note: this can be called with an Annotation or AnnotationSet instead of `start` and `end`
          (see gatenlp._utils.support_annotation_or_set)

        Args:
          start: start offset of the span
          end: end offset of the span

        Returns:
          `True` if left-overlapping, `False` otherwise

        """
        return self.start <= start and self.end <= end

    @support_annotation_or_set
    def isrightoverlapping(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is overlapping with the given span, annotation or
        annotation set on the right, i.e. the first character is inside the span.

        Note: this can be called with an Annotation or AnnotationSet instead of `start` and `end`
          (see gatenlp._utils.support_annotation_or_set)

        Args:
          start: start offset of the span
          end: end offset of the span

        Returns:
          `True` if right-overlapping, `False` otherwise

        """
        return self.start >= start and self.end >= end

    @support_annotation_or_set
    def iscoextensive(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is coextensive with the given span, annotation or
        annotation set, i.e. has exactly the same start and end offsets.

        Note: this can be called with an Annotation or AnnotationSet instead of `start` and `end`
          (see gatenlp._utils.support_annotation_or_set)

        Args:
          start: start offset of the span
          end: end offset of the span

        Returns:
          `True` if coextensive, `False` otherwise

        """
        return self.start == start and self.end == end

    @support_annotation_or_set
    def iswithin(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is within the given span, annotation or
        annotation set, i.e. both the start and end offsets of this annotation
        are after the given start and before the given end.

        Note: this can be called with an Annotation or AnnotationSet instead of `start` and `end`
          (see gatenlp._utils.support_annotation_or_set)

        Args:
          start: start offset of the span
          end: end offset of the span

        Returns:
          `True` if within, `False` otherwise

        """
        return start <= self.start and end >= self.end

    @support_annotation_or_set
    def isbefore(self, start: int, end: int, immediately=False) -> bool:
        """
        Checks if this annotation is before the other span, i.e. the end of this annotation
        is before the start of the other annotation or span.

        Note: this can be called with an Annotation or AnnotationSet instead of `start` and `end`
          (see gatenlp._utils.support_annotation_or_set)

        Args:
            start: start offset of the span
            end: end offset of the span
            immediately: if true checks if this annotation ends immediately before the
                other one (Default value = False)

        Returns:
          True if before, False otherwise

        """
        if immediately:
            return self.end == start
        else:
            return self.end <= start

    @support_annotation_or_set
    def isafter(self, start: int, end: int, immediately=False) -> bool:
        """Checks if this annotation is after the other span, i.e. the start of this annotation
        is after the end of the other annotation or span.

        Note: this can be called with an Annotation or AnnotationSet instead of `start` and `end`
          (see gatenlp._utils.support_annotation_or_set)

        Args:
          start: start offset of the span
          end: end offset of the span
          immediately: if true checks if this annotation starts immediately after the other one
              (Default value = False)

        Returns:
          True if after, False otherwise

        """
        if immediately:
            return self.start == end
        else:
            return self.start >= end

    @support_annotation_or_set
    def isstartingat(self, start: int, end_: int) -> bool:
        """
        Return True iff the annotation starts at the given start offset.

        Args:
            start: start offset
            end_: only present so the method can be used with anything that can be interpreted as
                a span (AnnotationSet, Span)
        """
        return self._start == start

    @support_annotation_or_set
    def isendingwith(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is ending at the same offset as the given span or annotation.

        Args:
            start: start of the span (ignored)
            end: end of the span

        Returns:
            True if ending at the same offset as the span or annotation

        """
        return self._end == end

    @support_annotation_or_set
    def gap(self, start: int, end: int) -> int:
        """
        Return the gep between this annotation and the other annotation.
        This is the distance between
        the last character of the first annotation and the first character of the
        second annotation in
        sequence, so it is always independent of the order of the two annotations.

        This is negative if the annotations overlap.

        Note: this can be called with an Annotation or AnnotationSet instead of `start` and `end`
            (see gatenlp._utils.support_annotation_or_set)

        Args:
            start: start offset of span
            end: end offset of span

        Returns:
          size of gap

        """
        if self.start < start:
            # ann1start = self.start
            ann1end = self.end
            ann2start = start
            # ann2end = end
        else:
            ann2start = self.start
            # ann2end = self.end
            # ann1start = start
            ann1end = end
        return ann2start - ann1end

    @support_annotation_or_set
    def iscovering(self, start: int, end=None) -> bool:
        """Checks if this annotation is covering the given span, annotation or
        annotation set, i.e. both the given start and end offsets
        are after the start of this annotation and before the end of this annotation.

        If end is not given, then the method checks if start is an offset of a character
        contained in the span.

        Note: this can be called with an Annotation or AnnotationSet instead of `start` and `end`
          (see gatenlp._utils.support_annotation_or_set)

        Args:
          start: start offset of the span
          end: end offset of the span

        Returns:
          True if covering, False otherwise

        """
        if end is None:
            if self.end == self.start:
                return self.start == start
            else:
                return self.start <= start < self.end
        else:
            return self.start <= start and self.end >= end

    def to_dict(self, offset_mapper=None, offset_type=None, **kwargs):
        """
        Return a representation of this annotation as a nested map. This representation is
        used for several serialization methods.

        Args:
            offset_mapper: the offset mapper to use, must be specified if
                `offset_type` is specified.
            offset_type: the offset type to be used for the conversionm must be specified if
                `offset_mapper` is specified

        Returns:
            the dictionary representation of the Annotation
        """
        if (offset_mapper and not offset_type) or (not offset_mapper and offset_type):
            raise Exception(
                "offset_mapper and offset_type must be specified both or none"
            )
        if offset_mapper is not None:
            if offset_type == OFFSET_TYPE_JAVA:
                start = offset_mapper.convert_to_java(self._start)
                end = offset_mapper.convert_to_java(self._end)
            elif offset_type == OFFSET_TYPE_PYTHON:
                start = offset_mapper.convert_to_python(self._start)
                end = offset_mapper.convert_to_python(self._end)
            else:
                raise Exception(
                    f"Not a valid offset type: {offset_type}, must be 'p' or 'j'"
                )
        else:
            start = self._start
            end = self._end
        return {
            "type": self.type,
            "start": start,
            "end": end,
            "id": self.id,
            "features": self._features.to_dict(),
        }

    @staticmethod
    def from_dict(dictrepr, owner_set=None, **kwargs):
        """
        Construct an annotation object from the dictionary representation.

        Args:
          dictrepr: dictionary representation
          owner_set: the owning set the annotation should have (Default value = None)
          kwargs: ignored
        """
        ann = Annotation(
            dictrepr.get("start"),
            dictrepr.get("end"),
            dictrepr.get("type"),
            annid=dictrepr.get("id"),
            features=dictrepr.get("features"),
        )
        ann._owner_set = owner_set
        return ann

    def __copy__(self):
        return Annotation(
            self._start, self._end, self._type, annid=self._id, features=self._features
        )

    def copy(self):
        """
        Return a shallow copy of the annotation (features are shared).
        """
        return self.__copy__()

    def __deepcopy__(self, memo=None):
        if self._features is not None:
            fts = lib_copy.deepcopy(self._features.to_dict(), memo=memo)
        else:
            fts = None
        return Annotation(
            self._start, self._end, self._type, annid=self._id, features=fts
        )

    def deepcopy(self, memo=None):
        """
        Return a deep copy of the annotation (features and their values are copied as well).
        """
        return lib_copy.deepcopy(self, memo=memo)
