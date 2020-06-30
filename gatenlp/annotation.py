"""
An annotation is immutable, but the features it contains are mutable.
"""
import sys
from typing import List, Union, Dict, Set
from functools import total_ordering
from gatenlp.feature_bearer import FeatureBearer
from gatenlp.offsetmapper import OFFSET_TYPE_JAVA
from gatenlp.changelog import ChangeLog
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

    # NOTE: we deliberately do NOT expose _features as a propery features so that people do not
    # do ann.features["x"]=1 but do ann.set_feature("x",1) instead!

    @property
    def id(self):
        return self._id

    def __init__(self, start: int, end: int, annot_type: str, annot_id: int,
                 owner_set: "AnnotationSet" = None,
                 changelog: ChangeLog = None, features=None):
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
        :param changelog: a changelog, if changes to the features should get recorded
        :param features: an initial collection of features, None for no features.
        """
        super().__init__(features)
        self._gatenlp_type = "Annotation"
        # print("Creating Ann with changelog {} ".format(changelog), file=sys.stderr)
        self.changelog = changelog
        self._type = annot_type
        self._start = start
        self._end = end
        self._id = annot_id
        # the annotation set that "owns" this annotation, if any. This information is ONLY needed
        # if a changelog is used to log the changes to the annotations feature set.  Note that an annotation
        # can still exist after it has been deleted from a set, and if a feature gets changed then,
        # the log will contain an entry for this. The receiver of the log has to silently ignore
        # feature changes to non-existing annotations.
        self._owner_set = None

    # TODO: for now at least, make sure only simple JSON serialisable things are used! We do NOT
    # allow any user specific types in order to make sure what we create is interchangeable with GATE.
    # In addition we do NOT allow None features.
    # So a feature name always has to be a string (not None), the value has to be anything that is json
    # serialisable (except None keys for maps).
    # For performance reasons we check the feature name but not the value (maybe make checking optional
    # on by default but still optional?)
    def _log_feature_change(self, command: str, feature: str = None, value=None) -> None:
        if self.changelog is None:
            return
        ch = {
            "command": command,
            "type": "annotation",
            "set": self._owner_set.name,
            "id": self.id}
        if feature is not None:
            ch["feature"] = feature
        if value is not None:
            ch["value"] = value
        self.changelog.append(ch)

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
            if self.end < other.end:
                return True
            elif self.end > other.end:
                return False
            else:
                if self.type < other.type:
                    return True
                elif self.type > other.type:
                    return False
                else:
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

    def is_inside(self, offset: int) -> bool:
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
        return self.is_inside(start) or self.is_inside(end - 1)

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
    def is_covering(self, start: int, end: int) -> bool:
        """
        Checks if this annotation is covering the given span, annotation or
        annotation set, i.e. both the given start and end offsets
        are after the start of this annotation and before the end of this annotation.

        :param start: start offset of the span
        :param end: end offset of the span
        :return: True if within, False otherwise
        """
        return self.start <= start and self.end >= end

    def _json_repr(self, **kwargs) -> Dict:
        if "offset_mapper" in kwargs:
            om = kwargs["offset_mapper"]
            to_type = kwargs["offset_type"]
            if to_type == OFFSET_TYPE_JAVA:
                start = om.convert_to_java(self.start)
                end = om.convert_to_java(self.end)
            else:
                start = om.convert_to_python(self.start)
                end = om.convert_to_python(self.end)
        else:
            start = self.start
            end = self.end
        return {
            "start": start,
            "end": end,
            "type": self.type,
            "id": self.id,
            "features": self._features,
            "gatenlp_type": self.gatenlp_type  # TODO: get rid of this!!
        }

    @staticmethod
    def _from_json_map(jsonmap, **kwargs) -> "Annotation":
        ann = Annotation(jsonmap.get("start"), jsonmap.get("end"), jsonmap.get("type"), jsonmap.get("id"),
                         features=jsonmap.get("features"))
        return ann

    # def __setattr__(self, key, value):
    #     """
    #     Prevent start, stop, type and annotation id from getting overridden, once they have been
    #     set.
    #     :param key: attribute to set
    #     :param value: value to set attribute to
    #     :return:
    #     """
    #     print(f"Trying to set {key} to {value}")
    #     if key == "start" or key == "end" or key == "type" or key == "id":
    #         if self.__getattribute__(key) is None:
    #             print("Seems this is Null")
    #             super().__setattr__(key, value)
    #         else:
    #             raise Exception("Annotation attributes cannot get changed after being set")
    #     else:
    #         super().__setattr__(key, value)

    def to_dict(self):
        return {
            "type": self.type,
            "start": self.start,
            "end": self.end,
            "id": self.id,
            "features": self._features,
        }

    @staticmethod
    def from_dict(dictrepr, owner_set=None, changelog=None):
        ann = Annotation(
            start=dictrepr.get("start"),
            end=dictrepr.get("end"),
            annot_type=dictrepr.get("type"),
            annot_id=dictrepr.get("id"),
            owner_set=owner_set,
            changelog=changelog,
            features=dictrepr.get("features")
        )
        return ann
