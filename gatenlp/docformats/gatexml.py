"""
Support for loading and saving documents in the original GATE XML format
"""

# NOTE: this is very low priority, as we should be able to use a java command to always convert from gatexml to
# gatesimplejson or maybe flatbuffers?

def load(fp):
    """
    Load gatedocument from the given file.
    :param fp: file-like object
    :return:
    """
    pass

def dump(fp, obj):
    """
    Save document to file in original GATE XML format.
    :param fp:
    :param obj:
    :return:
    """
    pass