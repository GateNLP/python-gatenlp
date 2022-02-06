"""
Module that implements the various ways of how to save and load documents and change logs.
"""
import os
from gatenlp.serialization.default_json import JsonSerializer
from gatenlp.serialization.default_msgpack import MsgPackSerializer
from gatenlp.serialization.default_pickle import PickleSerializer
from gatenlp.serialization.default_plaintext import PlainTextSerializer
from gatenlp.serialization.default_tweetv1 import TweetV1Serializer
from gatenlp.serialization.default_yaml import YamlSerializer
from gatenlp.serialization.default_gatexml import GateXmlLoader
from gatenlp.serialization.default_htmlannviewer import HtmlAnnViewerSerializer
from gatenlp.serialization.default_htmlloader import HtmlLoader

# TODO: when loading from a URL, allow for deciding on the format based on the mime type!
# So if we do not have the format, we should get the header for the file, check the mime type and see
# if  we have a loder registered for that and then let the loader do the rest of the work. This may
# need loaders to be able to use an already open stream.


def determine_loader(
    clazz, from_ext=None, from_mem=None, offset_mapper=None, gzip=False, **kwargs
):
    """

    Args:
      clazz:
      from_ext: (Default value = None)
      from_mem: (Default value = None)
      offset_mapper: (Default value = None)
      gzip: (Default value = False)
      **kwargs:

    Returns:

    """
    if from_mem:
        first = from_mem[0]
    else:
        with open(from_ext, "rt") as infp:
            first = infp.read(1)
    if first == "{":
        return JsonSerializer.load(
            clazz,
            from_ext=from_ext,
            from_mem=from_mem,
            offset_mapper=offset_mapper,
            gzip=gzip,
            **kwargs,
        )
    else:
        return MsgPackSerializer.load(
            clazz,
            from_ext=from_ext,
            from_mem=from_mem,
            offset_mapper=offset_mapper,
            gzip=gzip,
            **kwargs,
        )


DOCUMENT_SAVERS = {
    "text/plain": PlainTextSerializer.save,
    "text/plain+gzip": PlainTextSerializer.save_gzip,
    "text": PlainTextSerializer.save,
    "json": JsonSerializer.save,
    "jsongz": JsonSerializer.save_gzip,
    "bdocjs": JsonSerializer.save,
    "pickle": PickleSerializer.save,
    "bdocjsgz": JsonSerializer.save_gzip,
    "text/bdocjs": JsonSerializer.save,
    "text/bdocjs+gzip": JsonSerializer.save_gzip,
    "yaml": YamlSerializer.save,
    "bdocym": YamlSerializer.save,
    "yamlgz": YamlSerializer.save_gzip,
    "text/bdocym": YamlSerializer.save,
    "text/bdocym+gzip+": YamlSerializer.save_gzip,
    "msgpack": MsgPackSerializer.save,
    "bdocmp": MsgPackSerializer.save,
    "tweet-v1": TweetV1Serializer.save,
    "text/bdocmp": MsgPackSerializer.save,
    "application/msgpack": MsgPackSerializer.save,
    "html-ann-viewer": HtmlAnnViewerSerializer.save,
}
DOCUMENT_LOADERS = {
    "json": JsonSerializer.load,
    "jsongz": JsonSerializer.load_gzip,
    "bdocjs": JsonSerializer.load,
    "bdocjsgz": JsonSerializer.load_gzip,
    "text/bdocjs": JsonSerializer.load,
    "text/bdocjs+gzip": JsonSerializer.load_gzip,
    "yaml": YamlSerializer.load,
    "yamlgz": YamlSerializer.load_gzip,
    "bdocym": YamlSerializer.load,
    "bdocymzg: ": YamlSerializer.load_gzip,
    "text/bdocym": YamlSerializer.load,
    "text/bdocym+gzip": YamlSerializer.load_gzip,
    "msgpack": MsgPackSerializer.load,
    "bdocmp": MsgPackSerializer.load,
    "application/msgpack": MsgPackSerializer.load,
    "text/bdocmp": MsgPackSerializer.load,
    "jsonormsgpack": determine_loader,
    "text/plain": PlainTextSerializer.load,
    "text/plain+gzip": PlainTextSerializer.load_gzip,
    "text": PlainTextSerializer.load,
    "text/html": HtmlLoader.load,
    "html": HtmlLoader.load,
    "html-rendered": HtmlLoader.load_rendered,
    "gatexml": GateXmlLoader.load,
    "tweet-v1": TweetV1Serializer.load,
    "pickle": PickleSerializer.load,
}
CHANGELOG_SAVERS = {
    "json": JsonSerializer.save,
    "text/bdocjs+gzip": JsonSerializer.save_gzip,
    "text/bdocjs": JsonSerializer.save,
}
CHANGELOG_LOADERS = {
    "json": JsonSerializer.load,
    "text/bdocjs+gzip": JsonSerializer.load_gzip,
    "text/bdocjs": JsonSerializer.load,
}

# map extensions to document types
EXTENSIONS = {
    "bdocjs": "json",
    "bdocym": "yaml",
    "bdocym.gz": "text/bdocym+gzip",
    "bdoc.gz": "text/bdocjs+gzip",  # lets assume it is compressed json
    "bdoc": "jsonormsgpack",
    "bdocjs.gz": "text/bdocjs+gzip",
    "bdocjson": "json",
    "bdocmp": "msgpack",
    "txt": "text/plain",
    "txt.gz": "text/plain+gzip",
    "html": "text/html",
    "htm": "text/html",
    "pickle": "pickle",
}


def get_handler(filespec, fmt, handlers, saveload, what):
    """

    Args:
      filespec:
      fmt:
      handlers:
      saveload:
      what:

    Returns:

    """
    msg = f"Could not determine how to {saveload} {what} for format {fmt} in module gatenlp.serialization.default"
    if fmt:
        handler = handlers.get(fmt)
        if not handler:
            raise Exception(msg)
        return handler
    else:
        if not filespec:  # in case of save_mem
            raise Exception(msg)
        if isinstance(filespec, os.PathLike):
            wf = os.fspath(filespec)
        elif isinstance(filespec, str):
            wf = filespec
        else:
            raise Exception(msg)
        name, ext = os.path.splitext(wf)
        if ext == ".gz":
            ext2 = os.path.splitext(name)[1]
            if ext2:
                ext2 = ext2[1:]
            ext = ext2 + ext
        elif ext:
            ext = ext[1:]
        fmt = EXTENSIONS.get(ext)
        msg = f"Could not determine how to {saveload} {what} for format {fmt} and with " \
              "extension {ext} in module gatenlp.serialization.default"
        if not fmt:
            raise Exception(msg)
        handler = handlers.get(fmt)
        if not handler:
            raise Exception(msg)
        return handler


def get_document_saver(filespec, fmt):
    """

    Args:
      filespec:
      fmt:

    Returns:

    """
    return get_handler(filespec, fmt, DOCUMENT_SAVERS, "save", "document")


def get_document_loader(filespec, fmt):
    """

    Args:
      filespec:
      fmt:

    Returns:

    """
    return get_handler(filespec, fmt, DOCUMENT_LOADERS, "load", "document")


def get_changelog_saver(filespec, fmt):
    """

    Args:
      filespec:
      fmt:

    Returns:

    """
    return get_handler(filespec, fmt, CHANGELOG_SAVERS, "save", "changelog")


def get_changelog_loader(filespec, fmt):
    """

    Args:
      filespec:
      fmt:

    Returns:

    """
    return get_handler(filespec, fmt, CHANGELOG_LOADERS, "load", "changelog")
