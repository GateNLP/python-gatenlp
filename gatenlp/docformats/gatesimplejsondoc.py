"""
GATE-specific serialisation of documents.
"""


def load(fp):
    """
    Load a GATE SimpleJson document and return it.
    :param fp: a file-like object, as required by json.load
    :return:
    """
    # TODO: no matter what offset format the json document has, we always return as python format
    pass

def dump(fp, doc, offsets="python"):
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
    pass
