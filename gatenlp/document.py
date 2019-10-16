from __future__ import annotations
import collections
import sys
from typing import List, Tuple, Union, Callable, Dict, Optional, KeysView, ValuesView
from gatenlp.offsetmapper import OffsetMapper, OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
from gatenlp.annotation_set import AnnotationSet
from gatenlp.annotation import Annotation
from gatenlp.changelog import ChangeLog
from .feature_bearer import FeatureBearer


class _AnnotationSetsDict(collections.defaultdict):
    def __init__(self, changelog: ChangeLog = None, owner_doc: Document=None):
        super().__init__()
        self.changelog = changelog
        self.owner_doc = owner_doc

    def __missing__(self, key: str):
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
    * Offsets of all annotations can be changed from/to Java (from python index of unicode codepoint to Java index
      of UTF-16 code unit and back)
    * No part of the document has to be present, not even the text (this allows saving just the annotations separately
      from the text)
    * Once the text has been set, it is immutable (no support to edit text and change annotation offsets accordingly)
    """
    def __init__(self, text: str, features=None, changelog: ChangeLog = None):
        super().__init__(features)
        self.changelog = changelog
        self.annotation_sets = _AnnotationSetsDict(self.changelog, owner_doc=self)
        self._text = text
        self.offset_type = OFFSET_TYPE_PYTHON

    def _ensure_type_python(self) -> None:
        if self.offset_type != OFFSET_TYPE_PYTHON:
            raise Exception("Document cannot be used if it is not type PYTHON, use to_type(OFFSET_TYPE_PYTHON) first")

    def _fixup_annotations(self, method: Callable) -> None:
        annset_names = self.annotation_sets.keys()
        for annset_name in annset_names:
            annset = self.annotation_sets[annset_name]
            for ann in annset:
                ann.start = method(ann.start)
                ann.end = method(ann.end)

    def to_type(self, offsettype: str) -> None:
        if offsettype == self.offset_type:
            return
        if offsettype == OFFSET_TYPE_JAVA and self.offset_type == OFFSET_TYPE_PYTHON:
            # convert from currently python to java
            om1 = OffsetMapper(self._text)
            self._fixup_annotations(om1.convert_to_java)
            self.offset_type = OFFSET_TYPE_JAVA
        elif offsettype == OFFSET_TYPE_PYTHON and self.offset_type == OFFSET_TYPE_JAVA:
            # convert from currently java to python
            om1 = OffsetMapper(self._text)
            self._fixup_annotations(om1.convert_to_python)
            self.offset_type = OFFSET_TYPE_PYTHON
        else:
            raise Exception("Odd offset type")

    def set_changelog(self, chlog: ChangeLog) -> ChangeLog:
        """
        Make the document use the given changelog to record all changes
        from this moment on.
        :param chlog: the new changelog to use or None to not use any
        :return: the changelog used previously or None
        """
        oldchlog = self.changelog
        self.changelog = chlog
        # make sure all the inner data structures use that chlog as well:
        self.annotation_sets.changelog = chlog
        for k, v in self.annotation_sets.items():
            v.changelog = chlog
        return oldchlog

    @property
    def text(self) -> str:
        self._ensure_type_python()
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if self._text is None:
            self._text = value
        else:
            raise NotImplementedError("Text cannot be modified")

    def size(self) -> int:
        self._ensure_type_python()
        return int(len(self.text))

    def _log_feature_change(self, command: str, feature: str = None, value=None) -> None:
        if self.changelog is None:
            return
        ch = {"command": command}
        if feature is not None:
            ch["feature"] = feature
            ch["value"] = value
        self.changelog.append(ch)

    def __len__(self) -> int:
        """
        Return the length of the text.
        :return:
        """
        self._ensure_type_python()
        return len(self._text)

    # TODO: type annotation for span/int?
    def __getitem__(self, item) -> str:
        self._ensure_type_python()
        if isinstance(item, Annotation):
            return self.text[item.start:item.end]
        return self.text[item]

    def get_annotations(self, name: str = "") -> AnnotationSet:
        """
        Get the named annotation set, if name is not given or the empty string, the default annotation set.
        If the annotation set does not already exist, it is created.
        :return: the specified annotation set.
        """
        self._ensure_type_python()
        return self.annotation_sets[name]

    def get_annotation_set_names(self) -> KeysView[str]:
        """
        Return the set of known annotation set names.
        :return: annotation set names
        """
        self._ensure_type_python()
        return self.annotation_sets.keys()

    def __repr__(self) -> str:
        return "Document({},features={},anns={})".format(self.text, self.features, self.annotation_sets)

    def json_repr(self, **kwargs) -> Dict:
        """
        Return a JSON-representable version of this object
        :return: something JSON can serialise
        """
        offset_type = self.offset_type
        if "offset_type" in kwargs and kwargs["offset_type"] != offset_type:
            om = OffsetMapper(self._text)
            kwargs["offset_mapper"] = om
            offset_type = kwargs["offset_type"]
        return {
            "text": self._text,
            "features": self.features,
            # turn our special class into an ordinary map
            "annotation_sets": {name: annset.json_repr(**kwargs) for name, annset in self.annotation_sets.items()},
            "offset_type": offset_type
        }

    @staticmethod
    def from_json_map(jsonmap, **kwargs) -> Document:
        doc = Document(jsonmap.get("text"), features=jsonmap.get("features"))
        doc.annotation_sets = _AnnotationSetsDict()
        for k, v in jsonmap.get("annotation_sets").items():
            # print("Adding set {} of type {}".format(k, type(v)), file=sys.stderr)
            doc.annotation_sets[k] = v
        offset_type = jsonmap.get("offset_type")
        doc.offset_type = offset_type
        if offset_type == OFFSET_TYPE_JAVA:
            doc.to_type(OFFSET_TYPE_PYTHON)
        if "with_changelog" in kwargs:
            chlog = ChangeLog()
            doc.set_changelog(chlog)
        return doc
