"""
GATE-specific (de)serialisation of documents. This is called "simplejson" to make it easy
to keep it apart from the default JSON de/serialiser (which is used but extended).
"""
import json
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
        # we use duck-typing here to guess the type of the object
        if "command" in thedict or "change" in thedict:  # probably a request or change
            return thedict
        elif "text" in thedict:
            return Document.from_json_map(thedict, **kwargs)
        elif "start" in thedict and "id" in thedict:
            return Annotation.from_json_map(thedict, **kwargs)
        elif "annotations" in thedict and "max_annid" in thedict:
            return AnnotationSet.from_json_map(thedict, **kwargs)
        elif "changes" in thedict:
            return ChangeLog.from_json_map(thedict, **kwargs)
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


def loads(str, **kwargs):
    """
    Create gatenlp object from JSON string and return it.

    :param str: JSON string
    :return: the gatenlp object
    """
    return json.loads(str, object_hook=get_object_hook(**kwargs))


def dump(fp, obj, indent=None, **kwargs):
    """
    Write the given gatenlp object to the file.
    :param fp: a file like object as required by json.dump
    :param obj: the object to save
    :param indent: passed on to jsom.dump
    :param kwargs:
    :return:
    """
    json.dump(fp, obj, indent=indent, default=get_object_encoder(**kwargs))


def dumps(obj, indent=None, **kwargs):
    """
    Create JSON string representing the given object.
    :param obj: the object
    :param indent: passed on to json.dumps
    :param kwargs:
    offset_type: if specified and OFFSET_TYPE_JAVA, convert the offsets to java offsets in the JSON
    offset_mapper: if specified, used for the offset mapping if an offset mapper cannot otherwise be found
    :return: JSON string
    """
    return json.dumps(obj, indent=indent, default=get_object_encoder(**kwargs))

