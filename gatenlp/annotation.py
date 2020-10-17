"""
An annotation is immutable, but the features it contains are mutable.
"""
import sys
from typing import List, Union, Dict, Set, Tuple
import copy
from functools import total_ordering
# from gatenlp.feature_bearer import FeatureBearer, FeatureViewer
from gatenlp.features import Features
from gatenlp.offsetmapper import OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
from gatenlp._utils import support_annotation_or_set


@total_ordering
class Annotation:
    """An annotation represents information about a span of text. It contains the start and end
    offsets of the span, an "annotation type" and it is a feature bearer.
    In addition it contains an id which has no meaning for the annotation itself but is
    used to uniquely identify an annotation within the set it is contained in.
    All fields except the features are immutable, once the annotation has been created
    only the features can be changed.

    Args:

    Returns:

    """

    @property
    def type(self):
        """:return: the type of the annotation, immutable."""
        return self._type

    @property
    def start(self):
        """:return: the start offset of the annotation, immutable."""
        return self._start

    @property
    def end(self):
        """Returns the end offset of the annotation, immutable.
        
        :return:

        Args:

        Returns:

        """
        return self._end

    @property
    def features(self):
        """Get the features for the annotation.
        
        :return: the Features object.

        Args:

        Returns:

        """
        return self._features

    @property
    def id(self):
        """

        Args:

        Returns:
          :return:

        """
        return self._id

    @property
    def span(self) -> Tuple[int, int]:
        """Returns a tuple with the start and end offset of the annotation.
        
        :return: tuple of start and end offsets

        Args:

        Returns:

        """
        return self.start, self.end

    def __init__(
            self, start: int, end: int, anntype: str,
            features=None,
            annid: int = 0
    ):
        """
        Create a new annotation instance. NOTE: this should almost never be done directly
        and instead the method annotation_set.add should be used!
        Once an annotation has been created, the start, end, type and id fields must not
        be changed!

        :param start: start offset of the annotation
        :param end: end offset of the annotation
        :param anntype: annotation type
        :param features: an initial collection of features, None for no features.
        :param annid: the id of the annotation
        """
        if end < start:
            raise Exception(f"Cannot create annotation start={start}, end={end}, type={anntype}, id={annid}, features={features}: start > end")
        if not isinstance(annid, int):
            raise Exception(f"Cannot create annotation start={start}, end={end}, type={anntype}, id={annid}, features={features}: annid is not an int")
        if isinstance(features, int):
            raise Exception(f"Cannot create annotation start={start}, end={end}, type={anntype}, id={annid}, features={features}: features must not be an int")
        # super().__init__(features)
        if annid is not None and not isinstance(annid, int):
            raise Exception("Parameter annid must be an int, mixed up with features?")
        if features is not None and isinstance(features, int):
            raise Exception("Parameter features must not be an int: mixed up with annid?")
        self._owner_set = None
        self._features = Features(features, logger=self._log_feature_change)
        self._type = anntype
        self._start = start
        self._end = end
        self._id = annid

    def _changelog(self):
        """

        Args:

        Returns:
          :return: the changelog

        """
        if self._owner_set is not None:
            return self._owner_set.changelog

    # TODO: for now at least, make sure only simple JSON serialisable things are used! We do NOT
    # allow any user specific types in order to make sure what we create is interchangeable with GATE.
    # In addition we do NOT allow None features.
    # So a feature name always has to be a string (not None), the value has to be anything that is json
    # serialisable (except None keys for maps).
    # For performance reasons we check the feature name but not the value (maybe make checking optional
    # on by default but still optional?)
    def _log_feature_change(self, command: str, feature: str = None, value=None) -> None:
        """

        Args:
          command: str: 
          feature: str:  (Default value = None)
          value:  (Default value = None)

        Returns:

        """
        if self._changelog() is None:
            return
        command = "ann-"+command
        ch = {
            "command": command,
            "type": "annotation",
            "set": self._owner_set.name,
            "id": self.id}
        if feature is not None:
            ch["feature"] = feature
        if value is not None:
            ch["value"] = value
        self._changelog().append(ch)

    def __eq__(self, other) -> bool:
        """
        Two annotations are identical if they are the same object or if all the fields
        are equal.

        :param other: the object to compare with
        :return: if the annotations are equal
        """
        if not isinstance(other, Annotation):
            return False
        if self is other:
            return True
        return self.start == other.start and self.end == other.end and \
               self.type == other.type and self.id == other.id and self._features == other._features

    def __hash__(self):
        """
        The hash depends on the annotation ID and the owning set.

        :return: hash
        """
        return hash((self.id, self._owner_set))

    def __lt__(self, other) -> bool:
        """
        Comparison for sorting: this sorts by increasing start offset,  then increasing annotation id.
        Since annotation ids within a set are unique, this guarantees a unique order of annotations that
        come from an annotation set.
        NOTE: for now the other object has to be an instance of Annotation, duck typing is not supported!

        :param other: another annotation
        :return:
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

        :return: string representation
        """
        return "Annotation({},{},{},features={},id={})".format(self.start, self.end, self.type, self._features, self.id)

    @property
    def length(self) -> int:
        """The length of the annotation is the length of the offset span. Since the end offset is one after the last
        element, we return end-start. Note: this is deliberately not implemented as len(ann), as
        len(annset) returns the number of annotations in the set but annset.length() also returns the
        span length of the annotation set, so the method name for this is identical between annotations
        and annotation sets.
        
        :return:

        Args:

        Returns:

        """
        return self.end - self.start

    @support_annotation_or_set
    def isoverlapping(self, start: int, end: int) -> bool:
        """Checks if this annotation is overlapping with the given span, annotation or
        annotation set.
        An annotation is overlapping with a span if the first or last character
        is inside that span.

        Args:
          start: start offset of the span
          end: end offset of the span
          start: int: 
          end: int: 

        Returns:
          True if overlapping, False otherwise

        """
        return self.iscovering(start) or self.iscovering(end - 1)

    @support_annotation_or_set
    def iscoextensive(self, start: int, end: int) -> bool:
        """Checks if this annotation is coextensive with the given span, annotation or
        annotation set, i.e. has exactly the same start and end offsets.

        Args:
          start: start offset of the span
          end: end offset of the span
          start: int: 
          end: int: 

        Returns:
          True if coextensive, False otherwise

        """
        return self.start == start and self.end == end

    @support_annotation_or_set
    def iswithin(self, start: int, end: int) -> bool:
        """Checks if this annotation is within the given span, annotation or
        annotation set, i.e. both the start and end offsets of this annotation
        are after the given start and before the given end.

        Args:
          start: start offset of the span
          end: end offset of the span
          start: int: 
          end: int: 

        Returns:
          True if within, False otherwise

        """
        return start <= self.start and end >= self.end

    @support_annotation_or_set
    def isbefore(self, start: int, end: int, immediately=False) -> bool:
        """Checks if this annotation is before the other span, i.e. the end of this annotation
        is before the start of the other annotation or span.

        Args:
          start: start offset of the span
          end: end offset of the span
          immediately: if true checks if this annotation ends immediately before the other one (Default value = False)
          start: int: 
          end: int: 

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

        Args:
          start: start offset of the span
          end: end offset of the span
          immediately: if true checks if this annotation starts immediately after the other one (Default value = False)
          start: int: 
          end: int: 

        Returns:
          True if after, False otherwise

        """
        if immediately:
            return self.start == end
        else:
            return self.start >= end

    @support_annotation_or_set
    def gap(self, start: int, end: int):
        """Return the gep between this annotation and the other annotation. This is the distance between
        the last character of the first annotation and the first character of the second annotation in
        sequence, so it is always independent of the order of the two annotations.
        
        This is negative if the annotations overlap.

        Args:
          start: start offset of span
          end: end offset of span
          start: int: 
          end: int: 

        Returns:
          size of gap

        """
        if self.start < start:
            ann1start = self.start
            ann1end = self.end
            ann2start = start
            ann2end = end
        else:
            ann2start = self.start
            ann2end = self.end
            ann1start = start
            ann1end = end
        return ann2start - ann1end

    @support_annotation_or_set
    def iscovering(self, start: int, end: int = None) -> bool:
        """Checks if this annotation is covering the given span, annotation or
        annotation set, i.e. both the given start and end offsets
        are after the start of this annotation and before the end of this annotation.
        
        If end is not given, then the method checks if start is an offset of a character
        contained in the span.

        Args:
          start: start offset of the span
          end: end offset of the span
          start: int: 
          end: int:  (Default value = None)

        Returns:
          True if covering, False otherwise

        """
        if end is None:
            return self.start <= start < self.end
        else:
            return self.start <= start and self.end >= end

    def to_dict(self, offset_mapper=None, offset_type=None):
        """Return a representation of this annotation as a nested map. This representation is
        used for several serialization methods.

        Args:
          offset_mapper: used if an offset_type is also specified. (Default value = None)
          offset_type: return: (Default value = None)

        Returns:

        """
        if (offset_mapper and not offset_type) or (not offset_mapper and offset_type):
            raise Exception("offset_mapper and offset_type must be specified both or none")
        if offset_mapper is not None:
            if offset_type == OFFSET_TYPE_JAVA:
                start = offset_mapper.convert_to_java(self._start)
                end = offset_mapper.convert_to_java(self._end)
            elif offset_type == OFFSET_TYPE_PYTHON:
                start = offset_mapper.convert_to_python(self._start)
                end = offset_mapper.convert_to_python(self._end)
            else:
                raise Exception(f"Not a valid offset type: {offset_type}, must be 'p' or 'j'")
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
        """Construct an annotation object from the dictionary representation.

        Args:
          dictrepr: dictionary representation
          owner_set: the owning set the annotation should have (Default value = None)
          kwargs: ignored
          **kwargs: 

        Returns:

        """
        ann = Annotation(
            start=dictrepr.get("start"),
            end=dictrepr.get("end"),
            anntype=dictrepr.get("type"),
            annid=dictrepr.get("id"),
            features=dictrepr.get("features")
        )
        ann._owner_set = owner_set
        return ann

    def __copy__(self):
        return Annotation(self._start, self._end, self._type, annid=self._id, features=self._features)

    def copy(self):
        """

        Args:

        Returns:
          :return: shallow copy

        """
        return self.__copy__()

    def __deepcopy__(self, memo=None):
        if self._features is not None:
            fts = copy.deepcopy(self._features.to_dict(), memo=memo)
        else:
            fts = None
        return Annotation(self._start, self._end, self._type, annid=self._id, features=fts)

    def deepcopy(self):
        """

        Args:

        Returns:
          :return: deep copy

        """
        return copy.deepcopy(self)