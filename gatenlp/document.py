import collections
from typing import Callable, Dict, KeysView, Any
from gatenlp.offsetmapper import OffsetMapper, OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
from gatenlp.annotation_set import AnnotationSet
from gatenlp.annotation import Annotation
from gatenlp.changelog import *
from gatenlp.feature_bearer import FeatureBearer, FeatureViewer
import logging
import importlib
import copy

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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

    def __init__(self, text: str = None, features=None, changelog: ChangeLog = None):
        if text is not None:
            assert isinstance(text, str)
        if changelog is not None:
            assert isinstance(changelog, ChangeLog)
        super().__init__(features)
        self.changelog = changelog
        self._annotation_sets = dict()
        self._text = text
        self.offset_type = OFFSET_TYPE_PYTHON

    def _ensure_type_python(self) -> None:
        if self.offset_type != OFFSET_TYPE_PYTHON:
            raise Exception("Document cannot be used if it is not type PYTHON, use to_type(OFFSET_TYPE_PYTHON) first")

    def _fixup_annotations(self, method: Callable) -> None:
        annset_names = self._annotation_sets.keys()
        for annset_name in annset_names:
            annset = self._annotation_sets[annset_name]
            if annset._annotations is not None:
                for ann in annset._annotations.values():
                    ann._start = method(ann._start)
                    ann._end = method(ann._end)

    def to_offset_type(self, offsettype: str) -> OffsetMapper:
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

    def apply_changes(self, changes, handle_existing_anns=ADDANN_ADD_WITH_NEW_ID):
        """
        Apply changes from a ChangeLog to this document. `changes` can be a ChangeLog instance,
        a sequence of change objects (dicts) as stored in a ChangeLog instance, or a single change object.

        The document is modified in-place.

        :param changes: one or more changes
        :param handle_existing_anns: what to do if the change from the changelog tries to add an annotation
          with an annotation id that already exists in the target set.
        :return:
        """
        if isinstance(changes, dict):
            changes = [changes]
        elif isinstance(changes, ChangeLog):
            changes = changes.changes
        for change in changes:
            cmd = change.get("command")
            fname = change.get("feature")
            sname = change.get("set")
            annid = change.get("id")
            if cmd is None:
                raise Exception("Change without field 'command'")
            if cmd == ACTION_ADD_ANNSET:
                assert sname is not None
                self.get_annotations(sname)
            elif cmd == ACTION_ADD_ANN:
                assert sname is not None
                assert annid is not None
                anns = self.get_annotations(sname)
                ann = anns.get(annid)
                start = change.get("start")
                end = change.get("end")
                anntype = change.get("type")

                if ann is None:
                    anns.add(start, end, anntype, annid)
                else:
                    if handle_existing_anns == ADDANN_IGNORE:
                        pass
                    elif handle_existing_anns == ADDANN_ADD_WITH_NEW_ID:
                        anns.add(start, end, anntype)
                    elif handle_existing_anns == ADDANN_REPLACE_ANNOTATION:
                        anns.remove(annid)
                        anns.add(start, end, anntype, annid)
                    elif handle_existing_anns == ADDANN_UPDATE_FEATURES:
                        features = change.get("features")
                        ann.update_features(features)
                    elif handle_existing_anns == ADDANN_REPLACE_FEATURES:
                        features = change.get("features")
                        ann.clear_features()
                        ann.update_features(features)
                    elif handle_existing_anns == ADDANN_ADD_NEW_FEATURES:
                        features = change.get("features")
                        fns = ann.feature_names()
                        for f in features.keys():
                            if f not in fns:
                                ann.set_feature(f, features[f])

            elif cmd == ACTION_CLEAR_ANNS:
                assert sname is not None
                anns = self.get_annotations(sname)
                anns.clear()
            elif cmd == ACTION_CLEAR_ANN_FEATURES:
                assert sname is not None
                assert annid is not None
                anns = self.get_annotations(sname)
                ann = anns.get(annid)
                if ann is not None:
                    ann.clear_features()
                else:
                    pass # ignore, could happen with a detached annotation
            elif cmd == ACTION_CLEAR_DOC_FEATURES:
                self.clear_features()
            elif cmd == ACTION_DEL_ANN_FEATURE:
                assert sname is not None
                assert annid is not None
                anns = self.get_annotations(sname)
                ann = anns.get(annid)
                if ann is not None:
                    if fname is not None:
                        ann.del_feature(fname)
                else:
                    pass  # ignore, could happen with a detached annotation
            elif cmd == ACTION_DEL_DOC_FEATURE:
                assert fname is not None
                self.del_feature(fname)
            elif cmd == ACTION_DEL_ANN:
                assert sname is not None
                assert annid is not None
                anns = self.get_annotations(sname)
                anns.remove(annid)

    @property
    def features(self, as_dict=False):
        """
        Accesses the features as a FeatureViewer instance. Changes made on this object are
        reflected in the document and recorded in the change log, if there is one.

        :return: A FeatureViewer view of the document features.
        """
        return FeatureViewer(self._features, changelog=self.changelog, logger=self._log_feature_change)


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
        command = "doc-"+command
        ch = {"command": command}
        if command == "doc-feature:set":
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
        if isinstance(span, AnnotationSet):
            return self.text[span.start():span.end()]
        return self.text[span]

    def get_annotations(self, name: str = "") -> AnnotationSet:
        """
        Get the named annotation set, if name is not given or the empty string, the default annotation set.
        If the annotation set does not already exist, it is created.

        :param name: the annotation set name, the empty string is used for the "default annotation set".
        :return: the specified annotation set.
        """
        self._ensure_type_python()
        if name not in self._annotation_sets:
            annset = AnnotationSet(owner_doc=self, name=name)
            self._annotation_sets[name] = annset
            if self.changelog:
                self.changelog.append({
                    "command": "annotations:add",
                    "set": name})
            return annset
        else:
            return self._annotation_sets[name]

    def get_annotation_set_names(self) -> KeysView[str]:
        """
        Return the set of known annotation set names.

        :return: annotation set names
        """
        self._ensure_type_python()
        return list(self._annotation_sets.keys())
    
    def remove_annotation_set(self, name: str):
        """
        Completely remove the annotation set.

        :param name: name of the annotation set to remove
        :return:
        """
        if name not in self._annotation_sets:
            raise Exception(f"AnnotationSet with name {name} does not exist")
        del self._annotation_sets[name]
        if self.changelog:
            self.changelog.append({
                "command": "annotations:remove",
                "set": name})

    def __repr__(self) -> str:
        """
        String representation of the document, showing all content.

        :return: string representation
        """
        return "Document({},features={},anns={})".format(self.text, self._features, self._annotation_sets.__repr__())

    def __str__(self) -> str:
        asets = "["+",".join([f"'{k}':{len(v)}" for k, v in self._annotation_sets.items()])+"]"
        return "Document({},features={},anns={})".format(self.text, self._features, asets)

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
            "annotation_sets": {name: aset.to_dict() for name, aset in self._annotation_sets.items() },
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
        doc._features = dictrepr.get("features")
        annsets = {name: AnnotationSet.from_dict(adict, owner_doc=doc)
                   for name, adict in dictrepr.get("annotation_sets").items()}
        doc._annotation_sets = annsets
        return doc

    def save(self, destination, fmt=None, offset_type=None, mod="gatenlp.serialization.default", **kwargs):
        """
        Save the document to the destination file.

        :param destination: either a file name or something that has a write(string) method.
        :param fmt: serialization format, by default the format is inferred from the file extension.
        :param offset_type: store using the given offset type or keep the current if None
        :param mod: module where the document saver is implemented.
        :param kwargs: additional parameters for the document saver.
        :return:
        """
        if fmt is None or isinstance(fmt, str):
            m = importlib.import_module(mod)
            saver = m.get_document_saver(destination, fmt)
            saver(Document, self, to_ext=destination, offset_type=offset_type, **kwargs)
        else:
            # assume fmt is a callable to get used directly
            fmt(Document, self, to_ext=destination, offset_type=offset_type, **kwargs)

    def save_mem(self, fmt="json", offset_type=None, mod="gatenlp.serialization.default", **kwargs):
        """
        Serialize to a string or bytes in the given format.

        :param fmt: serialization format to use.
        :param offset_type: store using the given offset type or keep the current if None
        :param mod: module where the document saver is implemented.
        :param kwargs: additional parameters for the format.
        :return:
        """
        if not fmt:
            raise Exception("Format required.")
        if isinstance(fmt, str):
            m = importlib.import_module(mod)
            saver = m.get_document_saver(None, fmt)
            return saver(Document, self, to_mem=True, offset_type=offset_type, **kwargs)
        else:
            fmt(Document, self, to_mem=True, offset_type=offset_type, **kwargs)

    @staticmethod
    def load(source, fmt=None, mod="gatenlp.serialization.default", **kwargs):
        """
        Load or import a document from the given source. The source can be a file path or file name or
        a URL. If the type of the source is str, then if it starts with "http[s]://" it will get treated
        as a URL. In order to deliberatly use a file instead of a URL, create a pathlib Path, in order to
        deliberately use URL instead of a file parse the URL using urllib.

        NOTE: the offset type of the document is always converted to PYTHON when loading!

        :param source: the URL or file path to load from.
        :param fmt: the format of the source. By default the format is inferred by the file extension.
          The format can be a format memnonic like "json", "html", or a known mime type like "text/bdocjs".
        :param mod: the name of a module where the document loader is implemented.
        :param kwargs: additional format specific keyword arguments to pass to the loader
        :return: the loaded document
        """
        if fmt is None or isinstance(fmt, str):
            m = importlib.import_module(mod)
            loader = m.get_document_loader(source, fmt)
            doc = loader(Document, from_ext=source, **kwargs)
        else:
            doc = fmt(Document, from_ext=source, **kwargs)
        if doc.offset_type == OFFSET_TYPE_JAVA:
            doc.to_offset_type(OFFSET_TYPE_PYTHON)
        return doc

    @staticmethod
    def load_mem(source, fmt="json", mod="gatenlp.serialization.default", **kwargs):
        """
        Create a document from the in-memory serialization in source. Source can be a string or
        bytes, depending on the format.

        Note: the offset type is always converted to PYTHON when loading!

        :param source: the string/bytes to deserialize
        :param fmt: the format
        :param mod: the name of the module where the loader is implemented
        :param kwargs: additional arguments to pass to the loader
        :return:
        """
        if not fmt:
            raise Exception("Format required.")
        if isinstance(fmt, str):
            m = importlib.import_module(mod)
            loader = m.get_document_loader(None, fmt)
            doc = loader(Document, from_mem=source, **kwargs)
        else:
            doc = fmt(Document, from_mem=source, **kwargs)
        if doc.offset_type == OFFSET_TYPE_JAVA:
            doc.to_offset_type(OFFSET_TYPE_PYTHON)
        return doc

    def __copy__(self):
        """
        Creates a shallow copy except the changelog which is set to None.

        :return: shallow copy of the document
        """
        doc = Document(self._text)
        doc._annotation_sets = self._annotation_sets
        doc.offset_type = self.offset_type
        doc._features = self._features
        return doc

    def copy(self):
        """
        Creates a shallow copy except the changelog which is set to None.

        :return: shallow copy of the document
        """
        return self.__copy__()

    def __deepcopy__(self, memo):
        """
        Creates a deep copy, except the changelog which is set to None.

        :param memo: the memoization dictionary to use.

        :return: a deep copy of the document.
        """
        if self._features is not None:
            fts = copy.deepcopy(self._features, memo)
        else:
            fts = None
        doc = Document(self._text, features=fts)
        doc.changelog = None
        doc._annotation_sets = copy.deepcopy(self._annotation_sets, memo)
        doc.offset_type = self.offset_type
        return doc

    def deepcopy(self):
        """
        Creates a deep copy, except the changelog which is set to None.

        :param memo: the memoization dictionary to use.

        :return: a deep copy of the document.
        """
        return copy.deepcopy(self)

    def _repr_html_(self):
        """
        Render function for Jupyter notebooks. Returns the html-ann-viewer HTML.

        :return:
        """
        return self.save_mem(fmt="html-ann-viewer", notebook=True, offline=True)