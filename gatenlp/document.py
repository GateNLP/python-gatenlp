import collections

from .offsetmapping import OffsetMapper, OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
from .annotation_set import AnnotationSet
from .annotation import Annotation
from .feature_bearer import FeatureBearer
import gatenlp


class _AnnotationSetsDict(collections.defaultdict):
    def __init__(self, changelog=None, owner_doc=None):
        super().__init__()
        self.changelog = changelog
        self.owner_doc = owner_doc

    def __missing__(self, key):
        annset = AnnotationSet(name=key, changelog=self.changelog, owner_doc=self.owner_doc)
        self[key] = annset
        return annset


class Document(FeatureBearer):

    """
    Represent a GATE document. This is different from the original Java GATE representation in several ways:
    * the text is not mutable and can only be set at creation time, so there is no "edit" method
    * as a feature bearer, all the methods to set, get and manipulate features are part of this class, there is
      no separate "FeatureMap" to store them
    * does not support listener callbacks
    * there is no separate abstraction for "content", the only content possible is text which is a unicode string
      that can be acessed with the "text()" method
    * Spans of text can be directly accessed using doc[from:to]
    * features are not stored in a separate feature map object, but are directly set on the document, e.g.
      doc.set_feature("x",y) or doc.get_feature("x", defaultvalue)
    * Features may only have string keys and values which can be json-serialised
    * Annotation offsets by default are number of Unicde code points, this is different from Java where the offsets
      are UTF-16 Unicode code units
    * Offsets of all annotations can be changed from/to Java
    """
    def __init__(self, text, features=None, changelog=None):
        super().__init__(features)
        self.changelog = changelog
        self.annotation_sets = _AnnotationSetsDict(self.changelog, owner_doc=self)
        self._text = text
        self.offset_type = OFFSET_TYPE_PYTHON

    def _ensure_type_python(self):
        if self.offset_type != OFFSET_TYPE_PYTHON:
            raise Exception("Document cannot be used if it is not type PYTHON, use to_type(OFFSET_TYPE_PYTHON) first")

    def _fixup_annotations(self, method):
        annset_names = self.get_annotation_set_names()
        for annset_name in annset_names:
            annset = self.get_annotations(annset_name)
            for ann in annset:
                ann.start = method(ann.start)
                ann.end = method(ann.end)

        raise Exception("Not yet implemented :( :(")

    def to_type(self, offsettype):
        if offsettype == self.offset_type:
            return
        if offsettype == OFFSET_TYPE_JAVA and self.offset_type == OFFSET_TYPE_PYTHON:
            # convert from currently python to java
            om1 = OffsetMapper(self)
            self._fixup_annotations(om1.convert_from_python)
            self.offset_type = OFFSET_TYPE_JAVA
        elif offsettype == OFFSET_TYPE_PYTHON and self.offset_type == OFFSET_TYPE_JAVA:
            # convert from currently java to python
            om1 = OffsetMapper(self)
            self._fixup_annotations(om1.convert_from_java)
            self.offset_type = OFFSET_TYPE_PYTHON
        else:
            raise Exception("Odd offset type")

    @property
    def text(self):
        self._ensure_type_python()
        return self._text

    @text.setter
    def text(self, value):
        raise NotImplementedError("Text cannot be modified in a Python processing resource")

    def size(self):
        self._ensure_type_python()
        return int(len(self.text))

    def _log_feature_change(self, command, feature=None, value=None):
        if self.changelog is None:
            return
        ch = {"command": command}
        if feature is not None:
            ch["name"] = feature
            ch["value"] = value
        self.changelog.append(ch)

    def __len__(self):
        """
        Return the length of the text.
        :return:
        """
        self._ensure_type_python()
        return len(self._text)

    def __getitem__(self, item):
        self._ensure_type_python()
        if isinstance(item, Annotation):
            return self.text[item.start:item.end]
        return self.text[item]

    def get_annotations(self, name=""):
        """
        Get the named annotation set, if name is not given or the empty string, the default annotation set.
        If the annotation set does not already exist, it is created.
        :return: the specified annotation set.
        """
        self._ensure_type_python()
        return self.annotation_sets[name]

    def get_annotation_set_names(self):
        """
        Return the set of known annotation set names.
        :return: annotation set names
        """
        self._ensure_type_python()
        return self.annotation_sets.keys()

    def json_repr(self, **kwargs):
        """
        Return a JSON-representable version of this object
        :return: something JSON can serialise
        """
        # TODO: if we need to change the offsets, create the mapper here and add it to the kwargs
        offset_type = self.offset_type
        if "offset_type" in kwargs and kwargs["offset_type"] != offset_type:
            om = OffsetMapper(self)
            kwargs["offset_mapper"] = om
        return {
            "object_type": "gatenlp.Document",
            "gatenlp_version": gatenlp.__version__,
            "text": self._text,
            # turn our special class into an ordinary map
            "annotation_sets": {name: annset.json_repr(**kwargs) for name, annset in self.annotation_sets.items()},
            "offset_type": offset_type
        }