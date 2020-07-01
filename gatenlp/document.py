import collections
from typing import Callable, Dict, KeysView, Any
from gatenlp.offsetmapper import OffsetMapper, OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
from gatenlp.annotation_set import AnnotationSet
from gatenlp.annotation import Annotation
from gatenlp.changelog import ChangeLog
from gatenlp.feature_bearer import FeatureBearer
import gatenlp.serialization.default
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class _AnnotationSetsDict(collections.defaultdict):
    """
    A dict name to annotationset which creates and stores an empty annotation
    set on the fly when it is requested.
    """
    def __init__(self, owner_doc: "Document" = None):
        super().__init__()
        self.owner_doc = owner_doc

    @property
    def changelog(self):
        return self.owner_doc.changelog

    def __missing__(self, key: str):
        annset = AnnotationSet(name=key, owner_doc=self.owner_doc)
        self[key] = annset
        return annset

    def to_dict(self, **kwargs):
        return dict((key, val.to_dict(**kwargs)) for key, val in self.items())

    @staticmethod
    def from_dict(dictrepr: Dict, owner_doc: "Document" = None, **kwargs):
        asd = _AnnotationSetsDict(owner_doc=owner_doc)
        asd.update(((key, AnnotationSet.from_dict(val, owner_doc=owner_doc, **kwargs)) for key, val in dictrepr.items()))
        return asd


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

    :param text: the text of the document. The text can be None to indicate that no initial text should be set. Once
      the text has been set for a document, it is immutable and cannot be changed.
    :param features: the initial document features to set, a sequence of key/value tuples
    :param changelog: a ChangeLog instance to use to log changes.
    """

    def __init__(self, text: str, features=None, changelog: ChangeLog = None):
        super().__init__(features)
        self.gatenlp_type = "Document"
        self.changelog = changelog
        self.annotation_sets = _AnnotationSetsDict(owner_doc=self)
        self._text = text
        self.offset_type = OFFSET_TYPE_PYTHON

    def _ensure_type_python(self) -> None:
        if self.offset_type != OFFSET_TYPE_PYTHON:
            raise Exception("Document cannot be used if it is not type PYTHON, use to_type(OFFSET_TYPE_PYTHON) first")

    def _fixup_annotations(self, method: Callable) -> None:
        annset_names = self.annotation_sets.keys()
        for annset_name in annset_names:
            annset = self.annotation_sets[annset_name]
            if annset._annotations is not None:
                for ann in annset._annotations.values():
                    ann._start = method(ann._start)
                    ann._end = method(ann._end)

    def to_type(self, offsettype: str) -> None:
        """
        Convert all the offsets of all the annotations in this document to the
        required type, either OFFSET_TYPE_JAVA or OFFSET_TYPE_PYTHON. If the offsets
        are already of that type, this does nothing.

        NOTE: if the document has a ChangeLog, it is NOT also converted!

        The method returns the offset mapper if anything actually was converted,
        otherwise None.

        :param offsettype: either OFFSET_TYPE_JAVA or OFFSET_TYPE_PYTHON
        :return: offset mapper or None
        """
        om = None
        if offsettype == self.offset_type:
            return
        if offsettype == OFFSET_TYPE_JAVA and self.offset_type == OFFSET_TYPE_PYTHON:
            # convert from currently python to java
            om = OffsetMapper(self._text)
            self._fixup_annotations(om.convert_to_java)
            self.offset_type = OFFSET_TYPE_JAVA
        elif offsettype == OFFSET_TYPE_PYTHON and self.offset_type == OFFSET_TYPE_JAVA:
            # convert from currently java to python
            om = OffsetMapper(self._text)
            self._fixup_annotations(om.convert_to_python)
            self.offset_type = OFFSET_TYPE_PYTHON
        else:
            raise Exception("Odd offset type")
        return om


    def set_changelog(self, chlog: ChangeLog) -> ChangeLog:
        """
        Make the document use the given changelog to record all changes
        from this moment on.

        :param chlog: the new changelog to use or None to not use any
        :return: the changelog used previously or None
        """
        oldchlog = self.changelog
        self.changelog = chlog
        # the annotation sets access the changelog via the owning document fields and the annotations
        # indirectly via the owning annotation set field
        return oldchlog

    @property
    def text(self) -> str:
        """
        Get the text of the document. For a partial document, the text may be None.

        :return: the text of the document
        """
        self._ensure_type_python()
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """
        Set the text of the document. This is only possible as long as it has not been set
        yet, after that, the text is immutable.

        :param value: the text for the document
        :return:
        """
        if self._text is None:
            self._text = value
        else:
            raise NotImplementedError("Text cannot be modified")

    def size(self) -> int:
        """
        Return the size of the document text.
        Note: this will convert the type of the document to python!

        :return: size of the document (length of the text)
        """
        self._ensure_type_python()
        return int(len(self.text))

    def _log_feature_change(self, command: str, feature: str = None, value=None) -> None:
        if self.changelog is None:
            return
        ch = {"command": command, "type": "document"}
        if command == "feature:set":
            ch["feature"] = feature
            ch["value"] = value
        self.changelog.append(ch)

    def __len__(self) -> int:
        """
        Return the length of the text.
        Note: this will convert the type of the document to python!

        :return: the length of the document text
        """
        self._ensure_type_python()
        return len(self._text)

    def __getitem__(self, span) -> str:
        """
        Get the text for the given span.

        :param span: a single number, an offset range of the form from:to or an annotation.
        If annotation, uses the annotation's offset span.
        :return: the text of the span
        """
        self._ensure_type_python()
        if isinstance(span, Annotation):
            return self.text[span._start:span._end]
        return self.text[span]

    def get_annotations(self, name: str = "") -> AnnotationSet:
        """
        Get the named annotation set, if name is not given or the empty string, the default annotation set.
        If the annotation set does not already exist, it is created.

        :param name: the annotation set name, the empty string is used for the "default annotation set".
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
    
    def remove_annotation_set(self, name: str):
        """
        Completely remove the annotation set.
        :param name: name of the annotation set to remove
        :return:
        """
        del self.annotation_sets[name]
        if self.changelog:
            self.changelog.append({
                "command": "annotations:remove",
                "set": name})

    def __repr__(self) -> str:
        """
        String representation of the document, showing all content.

        :return: string representation
        """
        return "Document({},features={},anns={})".format(self.text, self._features, self.annotation_sets)

    def _json_repr(self, **kwargs) -> Dict:
        """
        Return a a simple map representation of this document for JSON to serialize.

        :return: something JSON can serialize
        """
        offset_type = self.offset_type
        if "offset_type" in kwargs and kwargs["offset_type"] != offset_type:
            om = OffsetMapper(self._text)
            kwargs["offset_mapper"] = om
            offset_type = kwargs["offset_type"]
        return {
            "text": self._text,
            "features": self._features,
            # turn our special class into an ordinary map
            "annotation_sets": {name: annset._json_repr(**kwargs) for name, annset in self.annotation_sets.items()},
            "offset_type": offset_type,
            "gatenlp_type": self.gatenlp_type
        }

    @staticmethod
    def _from_json_map(jsonmap: Dict[str, Any], **kwargs) -> "Document":
        """
        Construct a document instance from the JSON map representation we get.

        :param jsonmap: the map representation of a document used for JSON
        :param kwargs: any kwargs passed through from the load/loads method
        :return: a document instance
        """
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

    def to_dict(self, offset_type=None, **kwargs):
        """
        Convert this instance to a dictionary that can be used to re-create the instance with
        from_dict.
        NOTE: if there is an active changelog, it is not included in the output as this
        field is considered a transient field!

        :param offset_type: convert to the given offset type on the fly

        :return: the dictionary representation of this instance
        """
        # if the specified offset type is equal to what we have, do nothing, otherwise
        # create an offset mapper and pass it down to where we actually convert the annotations

        om = None
        if offset_type is not None:
            assert offset_type == OFFSET_TYPE_JAVA or offset_type == OFFSET_TYPE_PYTHON
            if offset_type != self.offset_type:
                if self._text is not None:
                    om = OffsetMapper(self._text)
        else:
            offset_type = self.offset_type
        return {
            "annotation_sets": self.annotation_sets.to_dict(offset_type=offset_type, **kwargs),
            "text": self._text,
            "features": self._features,
            "offset_type": offset_type,
        }

    @staticmethod
    def from_dict(dictrepr, **kwargs):
        """
        Return a Document instance as represented by the dictionary dictrepr.
        :param dictrepr:
        :return: the initialized Document instance
        """
        doc = Document(dictrepr.get("text"))
        doc.offset_type = dictrepr.get("offset_type")
        if doc.offset_type != OFFSET_TYPE_JAVA and doc.offset_type != OFFSET_TYPE_PYTHON:
            raise Exception("Invalid offset type, cannot load: ", doc.offset_type)
        # doc.changelog = ChangeLog.from_dict(dictrepr.get("changelog"))
        doc._features = dictrepr.get("features")
        doc.annotation_sets = \
            _AnnotationSetsDict.from_dict(dictrepr.get("annotation_sets"),
                                          #changelog=doc.changelog,
                                          owner_doc=doc, **kwargs)
        return doc

    def save(self, whereto, fmt="json", offset_type=None, mod=gatenlp.serialization.default, **kwargs):
        """
        Save the document in the given format.

        Additional keyword parameters for format "json":
        * as_array: boolean, if True stores as array instead of dictionary, using to


        :param whereto: either a file name or something that has a write(string) method.
        :param fmt: serialization format, one of "json", "msgpack" or "pickle"
        :param offset_type: store using the given offset type or keep the current if None
        :param mod: module to use
        :param **kwargs: additional parameters for the format
        :return:
        """
        ser = mod.FORMATS[fmt]
        ser.save(Document, self, to_file=whereto, offset_type=offset_type, **kwargs)

    def save_string(self, fmt="json", offset_type=None, mod=gatenlp.serialization.default, **kwargs):
        """
        Serialize and save to a string.

        Additional keyword parameters for format "json":
        * as_array: boolean, if True stores as array instead of dictionary, using to


        :param fmt: serialization format, one of "json", "msgpack" or "pickle"
        :param offset_type: store using the given offset type or keep the current if None
        :param mod: module to use
        :param **kwargs: additional parameters for the format
        :return:
        """
        ser = mod.FORMATS[fmt]
        return ser.save(Document, self, to_string=True, offset_type=offset_type, **kwargs)

    @staticmethod
    def load(wherefrom, fmt="json", offset_type=None, mod=gatenlp.serialization.default, **kwargs):
        """

        :param wherefrom:
        :param fmt:
        :param offset_type: make sure to store using the given offset type
        :param kwargs:
        :return:
        """
        ser = mod.FORMATS[fmt]
        doc = ser.load(Document, from_file=wherefrom, **kwargs)
        if doc.offset_type == OFFSET_TYPE_JAVA:
            doc.to_type(OFFSET_TYPE_PYTHON)
        return doc

    @staticmethod
    def load_string(wherefrom, fmt="json", mod=gatenlp.serialization.default, **kwargs):
        """

        Note: the offset type is always converted to PYTHON when loading!

        :param wherefrom: the string to deserialize
        :param fmt:
        :param kwargs:
        :return:
        """
        ser = mod.FORMATS[fmt]
        doc = ser.load(Document, from_string=wherefrom, **kwargs)
        if doc.offset_type == OFFSET_TYPE_JAVA:
            doc.to_type(OFFSET_TYPE_PYTHON)
        return doc