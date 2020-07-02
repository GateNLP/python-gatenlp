
import io
import json
from msgpack import pack, Unpacker
from gatenlp.document import Document, _AnnotationSetsDict
from gatenlp.annotation_set import AnnotationSet
from gatenlp.annotation import Annotation
from gatenlp.changelog import ChangeLog


class JsonSerializer:

    @staticmethod
    def save(clazz, inst, to_file=None, to_mem=None, offset_type=None, offset_mapper=None, **kwargs):
        d = inst.to_dict(offset_type=offset_type, offset_mapper=offset_mapper, **kwargs)
        if to_mem:
            return json.dumps(d)
        else:
            with open(to_file, "wt") as outfp:
                json.dump(d, outfp)

    @staticmethod
    def load(clazz, from_file=None, from_mem=None, offset_mapper=None, **kwargs):
        if from_mem:
            d = json.loads(from_mem)
            doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        else:
            with open(from_file, "rt") as infp:
                d = json.load(infp)
                # print("DEBUG: dict=", d)
                doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        return doc


MSGPACK_VERSION_HDR = "sm1"


class MsgPackSerializer:

    @staticmethod
    def document2stream(doc: Document, stream):
        pack(MSGPACK_VERSION_HDR, stream)
        pack(doc.offset_type, stream)
        pack(doc.text, stream)
        pack(doc._features, stream)
        pack(len(doc.annotation_sets), stream)
        for name, annset in doc.annotation_sets:
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
        setsdict = _AnnotationSetsDict(owner_doc=doc)
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
                annset[aid] = ann
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


FORMATS = dict(json=JsonSerializer, msgpack=MsgPackSerializer)