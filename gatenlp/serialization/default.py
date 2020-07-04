
import io
import os
import json
from msgpack import pack, Unpacker
from gatenlp.document import Document
from gatenlp.annotation_set import AnnotationSet
from gatenlp.annotation import Annotation
from gatenlp.changelog import ChangeLog
from gzip import open as gopen


class JsonSerializer:

    @staticmethod
    def save(clazz, inst, to_file=None, to_mem=None, offset_type=None, offset_mapper=None, gzip=False, **kwargs):
        d = inst.to_dict(offset_type=offset_type, offset_mapper=offset_mapper, **kwargs)
        if to_mem:
            if gzip:
                raise Exception("GZip compression not supported for in-memory loading")
            return json.dumps(d)
        else:
            if gzip:
                with gopen(to_file, "wt") as outfp:
                    json.dump(d, outfp)
            else:
                with open(to_file, "wt") as outfp:
                    json.dump(d, outfp)

    @staticmethod
    def save_gzip(clazz, inst, **kwargs):
        JsonSerializer.save(clazz, inst, gzip=True, **kwargs)

    @staticmethod
    def load(clazz, from_file=None, from_mem=None, offset_mapper=None, gzip=False, **kwargs):
        if from_mem:
            if gzip:
                raise Exception("GZip compression not supported for in-memory loading")
            d = json.loads(from_mem)
            doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        else:
            if gzip:
                with gopen(from_file, "rt") as infp:
                    d = json.load(infp)
            else:
                with open(from_file, "rt") as infp:
                    d = json.load(infp)
            doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        return doc

    @staticmethod
    def load_gzip(clazz, **kwargs):
        return JsonSerializer.load(clazz, gzip=True, **kwargs)


MSGPACK_VERSION_HDR = "sm1"


class MsgPackSerializer:

    @staticmethod
    def document2stream(doc: Document, stream):
        pack(MSGPACK_VERSION_HDR, stream)
        pack(doc.offset_type, stream)
        pack(doc.text, stream)
        pack(doc._features, stream)
        pack(len(doc._annotation_sets), stream)
        for name, annset in doc._annotation_sets:
            pack(name, stream)
            pack(annset.next_annid, stream)
            pack(len(annset), stream)
            for ann in annset.fast_iter():
                pack(ann.type, stream)
                pack(ann.start, stream)
                pack(ann.end, stream)
                pack(ann.id, stream)
                pack(ann.features, stream)

    @staticmethod
    def stream2document(stream):
        u = Unpacker(stream)
        version = u.unpack()
        if version != MSGPACK_VERSION_HDR:
            raise Exception("MsgPack data starts with wrong version")
        doc = Document()
        doc.offset_type = u.unpack()
        doc._text = u.unpack()
        doc._features = u.unpack()
        nsets = u.unpack()
        setsdict = dict()
        doc.annotation_sets = setsdict
        for iset in range(nsets):
            sname = u.unpack()
            if sname is None:
                sname = ""
            annset = AnnotationSet(name=sname, owner_doc=doc)
            annset._next_annid = u.unpack()
            nanns = u.unpack()
            for iann in range(nanns):
                atype = u.unpack()
                astart = u.unpack()
                aend = u.unpack()
                aid = u.unpack()
                afeatures = u.unpack()
                ann = Annotation(astart, aend, atype, annid=aid, features=afeatures)
                annset._annotations[aid] = ann
            setsdict[sname] = annset
        return doc

    @staticmethod
    def save(clazz, inst, to_file=None, to_mem=None, offset_type=None, offset_mapper=None, **kwargs):
        if isinstance(inst, Document):
            writer = MsgPackSerializer.document2stream
        elif isinstance(inst, ChangeLog):
            raise Exception("Not implemented yet")
        else:
            raise Exception("Object not supported")
        if to_mem:
            f = io.BytesIO()
        else:
            f = open(to_file, "wb")
        writer(inst, f)
        if to_mem:
            return f.getvalue()
        else:
            f.close()

    @staticmethod
    def load(clazz, from_file=None, from_mem=None, offset_mapper=None, **kwargs):
        if clazz == Document:
            reader = MsgPackSerializer.stream2document
        elif clazz == ChangeLog:
            raise Exception("Not implemented yet")
        else:
            raise Exception("Object not supported")
        if from_mem:
            f = io.BytesIO(from_mem)
        else:
            f = open(from_file, "rb")
        doc = reader(f)
        return doc


def determine_loader(clazz, from_file=None, from_mem=None, offset_mapper=None, gzip=False, **kwargs):
    first = None
    if from_mem:
        first = from_mem[0]
    else:
        with open(from_file, "rt") as infp:
            first = infp.read(1)
    if first == "{":
        return JsonSerializer.load(clazz, from_file=from_file, from_mem=from_mem, offset_mapper=offset_mapper,
                            gzip=gzip, **kwargs)
    else:
        return MsgPackSerializer.load(clazz, from_file=from_file, from_mem=from_mem, offset_mapper=offset_mapper,
                            gzip=gzip, **kwargs)


DOCUMENT_SAVERS = {
    "json": JsonSerializer.save,
    "text/bdocjs": JsonSerializer.save,
    "text/bdocjs+gzip": JsonSerializer.save_gzip,
    "msgpack": MsgPackSerializer.save,
    "application/msgpack": MsgPackSerializer.save,
}
DOCUMENT_LOADERS = {
    "json": JsonSerializer.load,
    "jsonormsgpack": determine_loader,
    "text/bdocjs": JsonSerializer.load,
    "text/bdocjs+gzip": JsonSerializer.load_gzip,
    "msgpack": MsgPackSerializer.load,
    "application/msgpack": MsgPackSerializer.load,
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

EXTENSIONS = {
    "bdocjs": "json",
    "bdoc": "jsonormsgpack",
    "bdocjs.gz": "text/bdocjs+gzip",
    "bdocjson": "json",
    "bdocmp": "msgpack"
}


def get_handler(filespec, fmt, handlers, saveload, what):
    msg = f"Could not determine how to {saveload} {what} for format {fmt} in module gatenlp.serialization.default"
    if fmt:
        handler = handlers.get(fmt)
        if not handler:
            raise Exception(msg)
        return handler
    else:
        if not filespec: # in case of save_mem
            raise Exception(msg)
        if isinstance(filespec, os.PathLike):
            wf = os.fspath(filespec)
        elif isinstance(filespec, str):
            wf = filespec
        else:
            raise Exception(msg)
        name,ext = os.path.splitext(wf)
        if ext == ".gz":
            ext2 = os.path.splitext(name)[1]
            if ext2:
                ext2 = ext2[1:]
            ext = ext2 + ext
        elif ext:
            ext = ext[1:]
        fmt = EXTENSIONS.get(ext)
        msg = f"Could not determine how to {saveload} {what} for format {fmt} and with extension {ext} in module gatenlp.serialization.default"
        if not fmt:
            raise Exception(msg)
        handler = handlers.get(fmt)
        if not handler:
            raise Exception(msg)
        return handler


def get_document_saver(filespec, fmt):
    return get_handler(filespec, fmt, DOCUMENT_SAVERS, "save", "document")


def get_document_loader(filespec, fmt):
    return get_handler(filespec, fmt, DOCUMENT_LOADERS, "load", "document")


def get_changelog_saver(filespec, fmt):
    return get_handler(filespec, fmt, CHANGELOG_SAVERS, "save", "changelog")


def get_changelog_loader(filespec, fmt):
    return get_handler(filespec, fmt, CHANGELOG_LOADERS, "load", "changelog")