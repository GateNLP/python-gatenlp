"""
GATE-specific (de)serialisation of documents. This is called "simplejson" to make it easy
to keep it apart from the default JSON de/serialiser (which is used but extended).
"""
import json as json_orig

# ujson would be fast, but does not support object_hook
# UPDATE: may be possible using the toDict method, see 
# https://github.com/ultrajson/ultrajson/issues/358
#try:
#    import ujson as json_ujson
#except:
#    json_ujson = None

# Too simplistic, does not support object_hook
# Repo has been archived: https://github.com/rtyler/py-yajl
# Not usable
#try:
#    import yajl as json_yajl
#except:
#    json_yajl = None

# yajl-py: pip install requires a manual installation of the underlying yajl C library,
# also seems to have trouble with Python 3 strings, unusuable here

try:
    import simplejson as json_simplejson
except:
    json_simplejson = None

import gzip
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
    # Todo: check https://realpython.com/python-json/#encoding-and-decoding-custom-python-objects and similar
    # again for how to do this correctly. Instead of providing our own default method, maybe override
    # the JSONEncoder class: has the advantage that we can fallback to the default default method!
    def object_encoder(obj):
        if hasattr(obj, "_json_repr"):
            return obj._json_repr(**kwargs)
        else:
            # objtypename = obj.__class__.__name__
            raise TypeError("Cannot JSON-serialise {} of type {}".format(obj, type(obj)))
    return object_encoder


def get_object_hook(**kwargs):
    """
    Returns a method that will try to convert the passed map into one of our objects
    :param kwargs: the kwargs to use for converting back.
    :return: the object hook function
    """
    def object_hook(thedict):
        # NOTE: we need to explicitly see the type, duck typing could get mislead
        # by other objects that just happen to have similar fields!
        if not "gatenlp_type" in thedict:
            return thedict
        ourtype = thedict.get("gatenlp_type")
        if ourtype == "Document":
            return Document._from_json_map(thedict, **kwargs)
        elif ourtype == "Annotation":
            return Annotation._from_json_map(thedict, **kwargs)
        elif ourtype == "AnnotationSet":
            return AnnotationSet._from_json_map(thedict, **kwargs)
        elif ourtype == "ChangeLog":
            return ChangeLog._from_json_map(thedict, **kwargs)
        else:
            return thedict
    return object_hook


def choose_json_lib(**kwargs):
    impl = kwargs.get("json_lib")
    if impl is None:
        return json_orig
#    elif impl == "ujson":
#        if json_ujson:
#            return json_ujson
#        else:
#            raise Exception("Library ujson could not be imported")
    elif impl == "json":
        if json_orig:
            return json_orig
        else:
            raise Exception("Library json could not be imported")
    elif impl == "simplejson":
        if json_simplejson:
            return json_simplejson
        else:
            raise Exception("Library simplejson could not be imported")
    else:
        raise Exception("Not a known json library: {}".format(impl))


def load(fp, **kwargs):
    """
    Load gatenlp object from fp, a file-like object and return it.
    :param fp: a file-like object, as required by json.load
    :param kwargs: one of 'json_lib', ...???
    :return: the gatenlp object
    """
    json = choose_json_lib(**kwargs)
    return json.load(fp, object_hook=get_object_hook(**kwargs))


def loads(str, **kwargs):
    """
    Create gatenlp object from JSON string and return it.

    :param str: JSON string
    :return: the gatenlp object
    """
    json = choose_json_lib(**kwargs)
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
    json = choose_json_lib(**kwargs)
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
    json = choose_json_lib(**kwargs)
    return json.dumps(obj, indent=indent, default=get_object_encoder(**kwargs))


def load_file(filename, **kwargs):
    """
    Shortcut for opening the file for reading and loading from the stream. If the filename ends with
    ".gz" the file is automatically uncompressed.
    :param filename: file to load
    :param kwargs:
    :return: the loaded object
    """
    if filename.endswith(".gz"):
        opener = gzip.open
        mode = "rt"
        encoding = "utf-8"
    else:
        opener = open
        mode = "rt"
        encoding = "utf-8"
    with opener(filename, mode, encoding=encoding) as fp:
        return load(fp, **kwargs)


def dump_file(obj, filename, indent=None, **kwargs):
    """
    Shortcut for opening the file for writing and dumping to the stream.
    If the file name ends with .gz, automatically compresses the output file.
    :param obj: the object to save
    :param filename: the file to write to
    :param indent: passed on to json.dump
    :param kwargs:
    :return:
    """
    if filename.endswith(".gz"):
        opener = gzip.open
        mode = "wt"
        encoding = "utf-8"
    else:
        opener = open
        mode = "wt"
        encoding = "utf-8"
    with opener(filename, mode, encoding=encoding) as fp:
        dump(obj, fp)
