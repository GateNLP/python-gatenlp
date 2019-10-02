"""
An annotation is immutable, but the features it contains are mutable.
"""
from .feature_bearer import FeatureBearer
from functools import total_ordering
from .offsetmapping import OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
import gatenlp


@total_ordering
class Annotation(FeatureBearer):
    """
    NOTE: the current way how annotations are implemented tries to minimize the effort for storing the annotation
    in an annotation set.
    !! This means that equality and hashing outside of an annotation set will not work as expected: the identify
    of an annotation only depends on its annotation ID, relative to the set it is contained in. So if you want
    to store annotations from different sets you need to use (annotationset, id) as the unique identifier!
    """

    # We use slots to avoid the dict and save memory if we have a large number of annotations
    __slots__ = ('changelog', 'type', 'start', 'end', 'features', 'id', 'owner_setname')

    def __init__(self, start, end, annot_type, annot_id, owner_setname=None, changelog=None, features=None):
        super().__init__(features)
        self.changelog = changelog
        self.type = annot_type
        self.start = start
        self.end = end
        self.id = annot_id
        self.owner_setname = owner_setname

    def _log_feature_change(self, command, feature=None, value=None):
        if self.changelog is None:
            return
        ch = {"command": command, "annotation_set": self.owner_setname, "annotation_id": self.id}
        if feature is not None:
            ch["name"] = feature
            ch["value"] = value
        self.changelog.append(ch)

    def __eq__(self, other):
        """
        Equality of annotations is only based on the annotation ID! This means you should never compare annotations
        from different sets directly!
        :param other: the object to compare with
        :return:
        """
        if not isinstance(other, Annotation):
            return False
        if self.id != other.id:
            return False
        else:
            return True

    def __hash__(self):
        """
        The hash only depends on the annotation ID! This means you should never add annotations from different sets
        directly to a map or other collection that depends on the hash.
        :return:
        """
        return hash(self.id)

    def __lt__(self, other):
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

    def __repr__(self):
        return "Annotation({},{},{},id={},features={})".format(self.start, self.end, self.type, self.id, self.features)

    def __len__(self):
        """
        The length of the annotation is the length of the offset span. Since the end offset is one after the last
        element, we return end-start-1
        :return:
        """
        return self.end - self.start - 1

    def json_repr(self, **kwargs):
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
            "object_type": "gatenlp.annotation.Annotation",
            "gatenlp_version": gatenlp.__version__,
            "start": start,
            "end": end,
            "type": self.type,
            "id": self.id,
            "features": self.features
        }

    @staticmethod
    def from_json_map(jsonmap, **kwargs):
        ann = Annotation(jsonmap.get("start"), jsonmap.get("end"), jsonmap.get("type"), jsonmap.get("id"),
                         features=jsonmap.get("features"))
        return ann


class AnnotationFromSet:
    """
    This class can be used to wrap Annotation objects such that they can be used for comparison and storing in
    containers that require the hash method. This class stores a reference to an annotation plus the name of
    the annotation set. NOTE: it is still possible to represent different annotations as identical
    AnnotationFromSet object if they come from different, but identically named sets (e.g. from different documents).
    It is the responsibility of the user to deal with this by using their own wrapping or other mechanism in
    those cases!!
    """
    def __init__(self, annotation, setname=None):
        """
        Tries to create an AnnotationFromSet from an annotation object and an optional annotation set name.
        If the annotation set name is not given, we try to get the name from the featuremap of the annotation,
        if the feature name does not know the name, an exception is thrown. If the annotation set name is given
        and the featuremap knows the name, they must be identical, otherwise an exception is thrown.
        If both are unspecified, an exception is thrown.
        :param annotation: the annotation to wrap
        :param setname: the name of the set where the annotation comes from
        :return:
        """
        setfromfeats = annotation.features.owner_set
        if setfromfeats is None and setname is None:
            raise Exception("No setname specified and not known to annotation either")
        if setfromfeats is not None and setname is not None and setfromfeats != setname:
            raise Exception("Specified setname {} is different from known name {}".format(setname, setfromfeats))
        if setname is None:
            setname = setfromfeats
        self.owner_set = setname
        self.annotation = annotation

    def __eq__(self, other):
        """
        Compare if two annotations from potentially different sets are equal. They are only equal if they come from
        the same set and have the same id.
        :param other: the annotationfromset to compare with
        :return:
        """
        if not isinstance(other, AnnotationFromSet):
            return False
        if self.owner_set != other.owner_set:
            return False
        if self.annotation != other.annotation:
            return False
        return True

    @staticmethod
    def from_anns(annotations, setname=None, astype=None):
        """
        Create a list/set from the list/set of annotations. If the annotations are not a list or not a set, then
        the collection type astype is used if specified, otherwise a set is returned.
        :param annotations:
        :param setname:
        :param astype: the type to return (list, set)
        :return:
        """
        if astype is None:
            if isinstance(annotations, list):
                ret = []
            elif isinstance(annotations, set):
                ret = set()
            else:
                ret = set()
        else:
            ret = astype()
        if hasattr(ret, "append"):
            for ann in annotations:
                ret.append(AnnotationFromSet(ann, setname=setname))
        elif hasattr(ret, "add"):
            for ann in annotations:
                ret.add(AnnotationFromSet(ann, setname=setname))
        else:
            raise Exception("Do not know how to handle type {}".format(astype))
        return ret


