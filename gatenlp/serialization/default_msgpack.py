"""
Module that implements the various ways of how to save and load documents and change logs.
"""
import io
import os
import sys
import yaml
from collections import defaultdict
# import ruyaml as yaml
try:
    from yaml import CFullLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import FullLoader as Loader, Dumper
yaml_loader = yaml.Loader
yaml_dumper = yaml.Dumper
from random import choice
from string import ascii_uppercase
from msgpack import pack, Unpacker
from gatenlp.document import Document
from gatenlp.annotation_set import AnnotationSet
from gatenlp.annotation import Annotation
from gatenlp.changelog import ChangeLog
from gatenlp.features import Features
from gatenlp.utils import get_nested
from gatenlp.urlfileutils import is_url, get_str_from_url, get_bytes_from_url
from gzip import open as gopen, compress, decompress
from bs4 import BeautifulSoup
from gatenlp.gatenlpconfig import gatenlpconfig
import bs4
import warnings
import pickle

try:
    from bs4 import GuessedAtParserWarning
    warnings.filterwarnings("ignore", category=GuessedAtParserWarning)
except ImportError as ex:
    pass


MSGPACK_VERSION_HDR = "sm2"


class MsgPackSerializer:
    """ """

    @staticmethod
    def document2stream(doc: Document, stream):
        """

        Args:
          doc: Document:
          stream:
          doc: Document:

        Returns:

        """
        pack(MSGPACK_VERSION_HDR, stream)
        pack(doc.offset_type, stream)
        pack(doc.text, stream)
        pack(doc.name, stream)
        pack(doc._features.to_dict(), stream)
        pack(len(doc._annotation_sets), stream)
        for name, annset in doc._annotation_sets.items():
            pack(name, stream)
            pack(annset._next_annid, stream)
            pack(len(annset), stream)
            for ann in annset.fast_iter():
                pack(ann.type, stream)
                pack(ann.start, stream)
                pack(ann.end, stream)
                pack(ann.id, stream)
                pack(ann.features.to_dict(), stream)

    @staticmethod
    def stream2document(stream):
        """

        Args:
          stream:

        Returns:

        """
        u = Unpacker(stream)
        version = u.unpack()
        if version != MSGPACK_VERSION_HDR:
            raise Exception("MsgPack data starts with wrong version")
        doc = Document()
        doc.offset_type = u.unpack()
        doc._text = u.unpack()
        doc.name = u.unpack()
        doc._features = Features(u.unpack())
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
        doc._annotation_sets = setsdict
        return doc

    @staticmethod
    def save(
        clazz,
        inst,
        to_ext=None,
        to_mem=None,
        offset_type=None,
        offset_mapper=None,
        **kwargs,
    ):
        """

        Args:
          clazz:
          inst:
          to_ext: (Default value = None)
          to_mem: (Default value = None)
          offset_type: (Default value = None)
          offset_mapper: (Default value = None)
          **kwargs:

        Returns:

        """
        if isinstance(inst, Document):
            writer = MsgPackSerializer.document2stream
        elif isinstance(inst, ChangeLog):
            raise Exception("Not implemented yet")
        else:
            raise Exception("Object not supported")
        if to_mem:
            f = io.BytesIO()
        else:
            f = open(to_ext, "wb")
        writer(inst, f)
        if to_mem:
            return f.getvalue()
        else:
            f.close()

    @staticmethod
    def load(clazz, from_ext=None, from_mem=None, offset_mapper=None, **kwargs):
        """

        Args:
          clazz:
          from_ext: (Default value = None)
          from_mem: (Default value = None)
          offset_mapper: (Default value = None)
          **kwargs:

        Returns:

        """
        if clazz == Document:
            reader = MsgPackSerializer.stream2document
        elif clazz == ChangeLog:
            raise Exception("Not implemented yet")
        else:
            raise Exception("Object not supported")

        isurl, extstr = is_url(from_ext)
        if from_ext is not None:
            if isurl:
                from_mem = get_bytes_from_url(extstr)
        if from_mem:
            f = io.BytesIO(from_mem)
        else:
            f = open(extstr, "rb")
        doc = reader(f)
        return doc

