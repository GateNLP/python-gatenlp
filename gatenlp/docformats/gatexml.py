"""
Support for loading and saving documents in the original GATE XML format
"""

# NOTE: this is very low priority, as we should be able to use a java command to always convert from gatexml to
# gatesimplejson or maybe flatbuffers?
# Note that this format uses the node elements to indicate where the annotations start and end
# so we need not worry about any offset numbers


def load(fp):
    """
    Load gatedocument from the given file.
    :param fp: file-like object
    :return:
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
