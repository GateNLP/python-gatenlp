"""
GATE-specific serialisation of documents.
"""
import json
from ..offsetmapping import OFFSET_TYPE_PYTHON, OFFSET_TYPE_JAVA, OffsetMapper


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

def load(fp, offset_type=OFFSET_TYPE_PYTHON):
    """
    Load a GATE SimpleJson document and return it.
    :param fp: a file-like object, as required by json.load
    :return:
    """
    # TODO: no matter what offset format the json document has, we always return as python format
    pass

def dump(fp, obj, offset_type=OFFSET_TYPE_PYTHON):
    # TODO: !!!! maybe use this for both documents and change logs.
    # TODO: !!! for change logs too, we need to decide on how to convert the offsets. For this, the
    # changelog needs to know about the document it refers to. 
    """
    Write the given document to the file.
    :param fp: a file like object as required by json.dump
    :param doc: the document to save
    :return:
    """
    # TODO: offsets by default get saved as python (if they are currently java, get converted first),
    # but we could specify here to save as java
    json.dump(fp, obj, default=get_object_encoder(offset_type=offset_type))


def dumps(doc, offset_type=OFFSET_TYPE_PYTHON):
    # NOTE: this will handle dumping a document, but if e.g. just a set or just an annotation
    # should get serialised, we also need to create the object mapper needed for changing the offsets, if needed
    # and pass it to the get_object_encoder method as kwarg offset_mapper
    return json.dumps(doc, indent=2, default=get_object_encoder(offset_type=offset_type))
