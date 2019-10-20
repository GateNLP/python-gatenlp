"""
For now, a placeholder to remind us looking into whether it makes sense to use flatbuffers as an additional
storage/wire format. May be more compact and much faster than json or even bson.
"""


def load(fp):
    """
    Load gatedocument from the given file.
    :param fp: file-like object
    :return: the object
    """
    raise Exception("Not yet implemented!")


def dump(fp, obj):
    """
    Save document to file in original GATE XML format.
    :param fp:
    :param obj:
    :return:
    """
    raise Exception("Not yet implemented!")
