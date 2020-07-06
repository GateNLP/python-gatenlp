"""
An annotation is immutable, but the features it contains are mutable.
"""
import sys
from typing import List, Union, Dict, Set
import copy
from functools import total_ordering
from gatenlp.feature_bearer import FeatureBearer, FeatureViewer
from gatenlp.offsetmapper import OFFSET_TYPE_JAVA
from gatenlp._utils import support_annotation_or_set


@total_ordering
class Annotation(FeatureBearer):
    """
    An annotation represents information about a span of text. It contains the start and end
    offsets of the span, an "annotation type" and it is a feature bearer.
    In addition it contains an id which has no meaning for the annotation itself but is
    used to uniquely identify an annotation within the set it is contained in.
    All fields except the features are immutable, once the annotation has been created
    only the features can be changed.
    """

    @property
    def type(self):
        return self._type

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    # TODO: we should get rid of this attribute completely!
    @property
    def gatenlp_type(self):
        return self._gatenlp_type

    @property
    def features(self):
        return FeatureViewer(self._features, changelog=self.changelog, logger=self._log_feature_change)

    @property
    def id(self):
        return self._id

    def __init__(self, start: int, end: int, annot_type: str,
                 annid: int = 0,
                 features=None):
        """
        Create a new annotation instance. NOTE: this should almost never be done directly
        and instead the method annotation_set.add should be used!
        Once an annotation has been created, the start, end, type and id fields must not
        be changed!
        :param start: start offset of the annotation
        :param end: end offset of the annotation
        :param annot_type: annotation type
        :param annot_id: the id of the annotation
        :param owner_set: the containing annotation set
        :param features: an initial collection of features, None for no features.
        """
        assert end > start
        assert isinstance(annid, int)
        assert not isinstance(features, int)  # avoid mixing up the two parameters!
        super().__init__(features)
        self._gatenlp_type = "Annotation"
        # print("Creating Ann with changelog {} ".format(changelog), file=sys.stderr)
        self._type = annot_type
        self._start = start
        self._end = end
        self._id = annid
        self._owner_set = None

    def _changelog(self):
        """
        Return the changelog of the owning set, if there is one, or None.
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
        # The old way to test for equality simply checked if owning set and id where identical
        #if self._owner_set != other._owner_set:
        #    return False
        #if self.id != other.id:
        #    return False
        #else:
        #    return True

    def __hash__(self):
        """
        The hash depends on the annotation ID and the owning set.
        :return: hash
        """
        return hash((self.id, self._owner_set))

    def __lt__(self, other) -> bool:
        """
        Comparison for sorting: this sorts by increasing start offset, then increasing end offset, then increasing
        type name, then increasing annotation id.
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
            # start offset same, check end offset
            if self.end < other.end:
                return True
            elif self.end > other.end:
                return False
            else:
                # end offset also same, check type
                if self.type < other.type:
                    return True
                elif self.type > other.type:
                    return False
                else:
                    # type also same check id
                    if self.id < other.id:
                        return True
                    else:
                        return False

    def __repr__(self) -> str:
        """
        String representation of the annotation.
        :return: string representation
        """
        return "Annotation({},{},{},id={},features={})".format(self.start, self.end, self.type, self.id, self._features)

    def __len__(self) -> int:
        """
        The length of the annotation is the length of the offset span. Since the end offset is one after the last
        element, we return end-start-1
        :return:
        """
        return self.end - self.start - 1

    def contains_offset(self, offset: int) -> bool:
        """
        Check if the given offset falls somewhere inside the span of this annotation.
        :param offset: the offset to check
        :return: True if the offset is inside the span of this annotation
        """
        return self.start <= offset < self.end

    @support_annotation_or_set
    def is_overlapping(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is overlapping with the given span, annotation or
        annotation set.
        An annotation is overlapping with a span if the first or last character
        is inside that span.

        :param start: start offset of the span
        :param end: end offset of the span
        :return: True if overlapping, False otherwise
        """
        return self.contains_offset(start) or self.contains_offset(end - 1)

    @support_annotation_or_set
    def is_coextensive(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is coextensive with the given span, annotation or
        annotation set, i.e. has exactly the same start and end offsets.

        :param start: start offset of the span
        :param end: end offset of the span
        :return: True if coextensive, False otherwise
        """
        return self.start == start and self.end == end

    @support_annotation_or_set
    def is_within(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is within the given span, annotation or
        annotation set, i.e. both the start and end offsets of this annotation
        are after the given start and before the given end.

        :param start: start offset of the span
        :param end: end offset of the span
        :return: True if within, False otherwise
        """
        return start <= self.start and end >= self.end

    @support_annotation_or_set
    def is_before(self, start: int, end: int, immediately=False) -> bool:
        """
        Checks if this annotation is before the other span, i.e. the end of this annotation
        is before the start of the other annotation or span.

        :param start: start offset of the span
        :param end: end offset of the span
        :return: True if before, False otherwise
        """
        if immediately:
            return self.end == start
        else:
            return self.end <= start

    @support_annotation_or_set
    def is_after(self, start: int, end: int, immediately=False) -> bool:
        """
        Checks if this annotation is after the other span, i.e. the start of this annotation
        is after the end of the other annotation or span.

        :param start: start offset of the span
        :param end: end offset of the span
        :return: True if after, False otherwise
        """
        if immediately:
            return self.start == end
        else:
            return self.start >= end

    @support_annotation_or_set
    def gap(self, start: int, end: int):
        """
        Return the gep between this annotation and the other annotation. This is the distance between
        the last character of the first annotation and the first character of the second annotation in
        sequence, so it is always independent of the order of the two annotations.

        This is negative if the annotations overlap.

        :param start: start offset of span
        :param end: end offset of span
        :return: size of gap
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
    def is_covering(self, start: int, end: int = None) -> bool:
        """
        Checks if this annotation is covering the given span, annotation or
        annotation set, i.e. both the given start and end offsets
        are after the start of this annotation and before the end of this annotation.

        If end is not given, then the method checks if start is an offset of a character
        contained in the span.

        :param start: start offset of the span
        :param end: end offset of the span
        :return: True if within, False otherwise
        """
        if end is None:
            return self.start <= start < self.end
        else:
            return self.start <= start and self.end >= end

    def to_dict(self, offset_mapper=None, offset_type=None):
        if offset_mapper is not None:
            if offset_type == OFFSET_TYPE_JAVA:
                start = offset_mapper.convert_to_java(self._start)
                end = offset_mapper.convert_to_java(self._end)
            else:
                start = offset_mapper.convert_to_python(self._start)
                end = offset_mapper.convert_to_python(self._end)
        else:
            start = self._start
            end = self._end
        return {
            "type": self.type,
            "start": start,
            "end": end,
            "id": self.id,
            "features": self._features,
        }

    @staticmethod
    def from_dict(dictrepr, owner_set=None, **kwargs):
        ann = Annotation(
            start=dictrepr.get("start"),
            end=dictrepr.get("end"),
            annot_type=dictrepr.get("type"),
            annid=dictrepr.get("id"),
            features=dictrepr.get("features")
        )
        ann._owner_set = owner_set
        return ann

    def __copy__(self):
        return Annotation(self._start, self._end, self._type, self._id, features=self._features)

    def copy(self):
        return self.__copy__()

    def __deepcopy__(self, memo):
        if self._features is not None:
            fts = copy.deepcopy(self._features, memo)
        else:
            fts = None
        return Annotation(self._start, self._end, self._type, self._id, features=fts)

    def deepcopy(self):
        return copy.deepcopy(self)