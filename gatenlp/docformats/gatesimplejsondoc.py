"""
GATE-specific (de)serialisation of documents.
"""
import json
from ..offsetmapping import OFFSET_TYPE_PYTHON, OFFSET_TYPE_JAVA, OffsetMapper
from ..document import Document
from ..annotation import Annotation
from ..annotation_set import AnnotationSet
from ..changelog import ChangeLog


def get_object_encoder(**kwargs):
    """
    Returns a function for encoding our own objects. This simply checks if the object
    has the method "json_repr" and if yes, calls it with the kwargs we got.
    :return:
    """
    def object_encoder(obj):
        if hasattr(obj, "json_repr"):
            return obj.json_repr(**kwargs)
        else:
            raise TypeError("Cannot JSON-serialise {} of type {}".format(obj, type(obj)))
    return object_encoder


def get_object_hook(**kwargs):
    """
    Returns a method that will try to convert the passed map into one of our objects
    :param kwargs: the kwargs to use for converting back.
    :return: the object hook function
    """
    def object_hook(thedict):
        if "object_type" in thedict:
            obj_type = thedict["object_type"]
            # we check all the known types here
            if obj_type == "gatenlp.document.Document":
                return Document.from_json_map(thedict, **kwargs)
            elif obj_type == "gatenlp.annotation.Annotation":
                return Annotation.from_json_map(thedict, **kwargs)
            elif obj_type == "gatenlp.annotation_set.AnnotationSet":
                return AnnotationSet.from_json_map(thedict, **kwargs)
            elif obj_type == "gatenlp.changelog.ChangeLog":
                return ChangeLog.from_json_map(thedict, **kwargs)
            else:
                return thedict
        else:
            return thedict
    return object_hook


def load(fp, **kwargs):
    """
    Load gatenlp object from fp, a file-like object and return it.
    :param fp: a file-like object, as required by json.load
    :return: the gatenlp object
    """
    return json.load(fp, object_hook=get_object_hook(**kwargs))


def loads(str):
    """
    Create gatenlp object from JSON string and return it.
    :param str: JSON string
    :return: the gatenlp object
    """
    return json.loads(str, object_hook=get_object_hook())


def dump(fp, obj, offset_type=OFFSET_TYPE_PYTHON):
    """
    Write the given gatenlp object to the file.
    :param fp: a file like object as required by json.dump
    :param obj: the object to save
    :param offset_type: if specified and OFFSET_TYPE_JAVA, convert the offsets to java offsets in the JSON
    :return:
    """
    json.dump(fp, obj, default=get_object_encoder(offset_type=offset_type))


def dumps(obj, indent=None, offset_type=OFFSET_TYPE_PYTHON):
    """
    Create JSON string representing the given object.
    :param obj: the object
    :param indent: passed on to json.dumps
    :param offset_type: if specified and OFFSET_TYPE_JAVA, convert the offsets to java offsets in the JSON
    :return: JSON string
    """
    return json.dumps(obj, indent=indent, default=get_object_encoder(offset_type=offset_type))

