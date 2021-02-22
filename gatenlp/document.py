"""
Module that implements the Document class for representing gatenlp documents with
features and annotation sets.
"""

from typing import KeysView, Callable
import logging
import importlib
import copy as lib_copy
from gatenlp.annotation_set import AnnotationSet
from gatenlp.annotation import Annotation
from gatenlp.offsetmapper import OffsetMapper, OFFSET_TYPE_PYTHON, OFFSET_TYPE_JAVA
from gatenlp.features import Features
from gatenlp.utils import in_notebook
from gatenlp.changelog import ChangeLog

from gatenlp.changelog_consts import (
    ACTION_ADD_ANN,
    ACTION_ADD_ANNSET,
    ACTION_CLEAR_ANNS,
    ADDANN_UPDATE_FEATURES,
    ACTION_CLEAR_ANN_FEATURES,
    ACTION_CLEAR_DOC_FEATURES,
    ACTION_DEL_ANN,
    ACTION_DEL_ANN_FEATURE,
    ACTION_DEL_DOC_FEATURE,
    ACTION_SET_ANN_FEATURE,
    ACTION_SET_DOC_FEATURE,
    ADDANN_ADD_NEW_FEATURES,
    ADDANN_ADD_WITH_NEW_ID,
    ADDANN_IGNORE,
    ADDANN_REPLACE_ANNOTATION,
    ADDANN_REPLACE_FEATURES,
)


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Document:
    """
    Represent a GATE document. This is different from the original Java GATE representation in
    several ways:

    * the text is not mutable and can only be set at creation time, so there is no "edit" method

    * as a feature bearer, all the methods to set, get and manipulate features are part of this
      class, there is
      no separate "FeatureMap" to store them

    * does not support listener callbacks
    * there is no separate abstraction for "content", the only content possible is text which
      is a unicode string that can be acessed with the "text()" method
    * Spans of text can be directly accessed using doc[from:to]
    * Features may only have string keys and values which can be json-serialised
    * Annotation offsets by default are number of Unicde code points, this is different from Java
      where the offsets are UTF-16 Unicode code units
    * Offsets of all annotations can be changed from/to Java (from python index of unicode
      codepoint to Java index of UTF-16 code unit and back)
    * No part of the document has to be present, not even the text (this allows saving just
      the annotations separately from the text)
    * Once the text has been set, it is immutable (no support to edit text and change annotation
      offsets accordingly)

    Args:
        text: the text of the document. The text can be None to indicate that no initial text
          should be set. Once the text has been set for a document, it is immutable and cannot
          be changed.
      features: the initial document features to set, a sequence of key/value tuples
      changelog: a ChangeLog instance to use to log changes.
    """

    def __init__(self, text: str = None, features=None, changelog: ChangeLog = None):
        if text is not None:
            assert isinstance(text, str)
        if changelog is not None:
            assert isinstance(changelog, ChangeLog)
        self._changelog = changelog
        self._features = Features(features, logger=self._log_feature_change)
        self._annotation_sets = dict()
        self._text = text
        self.offset_type = OFFSET_TYPE_PYTHON
        self._name = ""

    @property
    def name(self):
        """ """
        return self._name

    @name.setter
    def name(self, val):
        """

        Args:
          val:

        Returns:

        """
        if val is None:
            val = ""
        if not isinstance(val, str):
            raise Exception("Name must be a string")
        self._name = val
        if self._changelog is not None:
            ch = {"command": "name:set"}
            ch["name"] = val
            self._changelog.append(ch)

    def _ensure_type_python(self) -> None:
        """ """
        if self.offset_type != OFFSET_TYPE_PYTHON:
            raise Exception(
                "Document cannot be used if it is not type PYTHON, "
                + "use to_type(OFFSET_TYPE_PYTHON) first"
            )

    def _fixup_annotations(self, method: Callable) -> None:
        """

        Args:
          method: Callable:

        Returns:

        """
        annset_names = self._annotation_sets.keys()
        for annset_name in annset_names:
            annset = self._annotation_sets[annset_name]
            if annset._annotations is not None:
                for ann in annset._annotations.values():
                    ann._start = method(ann._start)
                    ann._end = method(ann._end)

    def to_offset_type(self, offsettype: str) -> OffsetMapper:
        """Convert all the offsets of all the annotations in this document to the
        required type, either OFFSET_TYPE_JAVA or OFFSET_TYPE_PYTHON. If the offsets
        are already of that type, this does nothing.

        NOTE: if the document has a ChangeLog, it is NOT also converted!

        The method returns the offset mapper if anything actually was converted,
        otherwise None.

        Args:
          offsettype: either OFFSET_TYPE_JAVA or OFFSET_TYPE_PYTHON
          offsettype: str:

        Returns:
          offset mapper or None

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
        """Apply changes from a ChangeLog to this document. `changes` can be a ChangeLog instance,
        a sequence of change objects (dicts) as stored in a ChangeLog instance, or a single
        change object.

        The document is modified in-place.

        Args:
          changes: one or more changes
          handle_existing_anns: what to do if the change from the changelog tries to
              add an annotation with an annotation id that already exists in the target set.
              (Default value = ADDANN_ADD_WITH_NEW_ID)

        """
        if isinstance(changes, dict):
            changes = [changes]
        elif isinstance(changes, ChangeLog):
            changes = changes.changes
        for change in changes:
            cmd = change.get("command")
            fname = change.get("feature")
            fvalue = change.get("value")
            features = change.get("features")
            sname = change.get("set")
            annid = change.get("id")
            if cmd is None:
                raise Exception("Change without field 'command'")
            if cmd == ACTION_ADD_ANNSET:
                assert sname is not None
                self.annset(sname)
            elif cmd == ACTION_ADD_ANN:
                assert sname is not None
                assert annid is not None
                anns = self.annset(sname)
                ann = anns.get(annid)
                start = change.get("start")
                end = change.get("end")
                anntype = change.get("type")

                if ann is None:
                    anns.add(start, end, anntype, annid=annid, features=features)
                else:
                    if handle_existing_anns == ADDANN_IGNORE:
                        pass
                    elif handle_existing_anns == ADDANN_ADD_WITH_NEW_ID:
                        anns.add(start, end, anntype)
                    elif handle_existing_anns == ADDANN_REPLACE_ANNOTATION:
                        anns.remove(annid)
                        anns.add(start, end, anntype, annid)
                    elif handle_existing_anns == ADDANN_UPDATE_FEATURES:
                        ann.features.update(features)
                    elif handle_existing_anns == ADDANN_REPLACE_FEATURES:
                        ann.features.clear()
                        ann.features.update(features)
                    elif handle_existing_anns == ADDANN_ADD_NEW_FEATURES:
                        fns = ann.feature_names()
                        for f in features.keys():
                            if f not in fns:
                                ann.features[f] = features[f]

            elif cmd == ACTION_CLEAR_ANNS:
                assert sname is not None
                anns = self.annset(sname)
                anns.clear()
            elif cmd == ACTION_CLEAR_ANN_FEATURES:
                assert sname is not None
                assert annid is not None
                anns = self.annset(sname)
                ann = anns.get(annid)
                if ann is not None:
                    ann.features.clear()
                else:
                    pass  # ignore, could happen with a detached annotation
            elif cmd == ACTION_CLEAR_DOC_FEATURES:
                self.features.clear()
            elif cmd == ACTION_SET_ANN_FEATURE:
                assert fname is not None
                assert sname is not None
                assert annid is not None
                ann = self.annset(sname).get(annid)
                ann.features[fname] = fvalue
            elif cmd == ACTION_DEL_ANN_FEATURE:
                assert sname is not None
                assert annid is not None
                anns = self.annset(sname)
                ann = anns.get(annid)
                if ann is not None:
                    if fname is not None:
                        ann.features.pop(fname, None)
                else:
                    pass  # ignore, could happen with a detached annotation
            elif cmd == ACTION_DEL_DOC_FEATURE:
                assert fname is not None
                self.features.pop(fname, None)
            elif cmd == ACTION_DEL_ANN:
                assert sname is not None
                assert annid is not None
                anns = self.annset(sname)
                anns.remove(annid)
            elif cmd == ACTION_SET_DOC_FEATURE:
                assert fname is not None
                self.features[fname] = fvalue
            elif cmd == ACTION_CLEAR_DOC_FEATURES:
                self._features.clear()
            elif cmd == ACTION_DEL_DOC_FEATURE:
                assert fname is not None
                del self._features[fname]
            else:
                raise Exception("Unknown ChangeLog action: ", cmd)

    @property
    def features(self):
        """Accesses the features as a FeatureViewer instance. Changes made on this object are
        reflected in the document and recorded in the change log, if there is one.

        :return: A FeatureViewer view of the document features.

        Args:

        Returns:

        """
        return self._features

    @property
    def changelog(self):
        """Get the ChangeLog or None if no ChangeLog has been set.

        :return: the changelog

        Args:

        Returns:

        """
        return self._changelog

    @changelog.setter
    def changelog(self, chlog):
        """Make the document use the given changelog to record all changes
        from this moment on.

        Args:
          chlog: the new changelog to use or None to not use any

        Returns:
          the changelog used previously or None

        """
        oldchlog = self._changelog
        self._changelog = chlog
        return oldchlog

    @property
    def text(self) -> str:
        """Get the text of the document. For a partial document, the text may be None.

        :return: the text of the document

        Args:

        Returns:

        """
        self._ensure_type_python()
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """
        Set the text of the document. This is only possible as long as it has not been set
        yet, after that, the text is immutable.

        IMPORTANT: it is possible to add arbitrary annotations to a document which does not have any
        text. This is meant to allow handling of annotation-only representations.
        However, if the text is set after annotations have been added, annotation offsets are not
        checked and it is possible to thus create an invalid document where annotations refer to
        text ranges that do not exist!

        Args:
          value: the text for the document
          value: str:

        Returns:

        """
        if self._text is None:
            self._text = value
        else:
            raise NotImplementedError("Text cannot be modified")

    def _log_feature_change(
        self, command: str, feature: str = None, value=None
    ) -> None:
        """

        Args:
          command: str:
          feature: str:  (Default value = None)
          value:  (Default value = None)

        Returns:

        """
        if self._changelog is None:
            return
        command = "doc-" + command
        ch = {"command": command}
        if command == "doc-feature:set":
            ch["feature"] = feature
            ch["value"] = value
        self._changelog.append(ch)

    def __len__(self) -> int:
        """
        Return the length of the text.
        Note: this will convert the type of the document to python!

        :return: the length of the document text
        """
        self._ensure_type_python()
        if self._text is None:
            return 0
        else:
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
        if hasattr(span, "start") and hasattr(span, "end"):
            return self.text[span.start, span.end]
        return self.text[span]

    def annset(self, name: str = "") -> AnnotationSet:
        """
        Get the named annotation set, if name is not given or the empty string,
        the default annotation set.
        If the annotation set does not already exist, it is created.

        Args:
            name: the annotation set name, the empty string is used for the
                "default annotation set".
            name: str:  (Default value = "")

        Returns:
          the specified annotation set.

        """
        self._ensure_type_python()
        if name not in self._annotation_sets:
            annset = AnnotationSet(owner_doc=self, name=name)
            self._annotation_sets[name] = annset
            if self._changelog:
                self._changelog.append({"command": "annotations:add", "set": name})
            return annset
        else:
            return self._annotation_sets[name]

    def annset_names(self) -> KeysView[str]:
        """

        Args:

        Returns:
          :return: annotation set names

        """
        self._ensure_type_python()
        return list(self._annotation_sets.keys())

    def remove_annset(self, name: str):
        """Completely remove the annotation set.

        Args:
          name: name of the annotation set to remove
          name: str:

        Returns:

        """
        if name not in self._annotation_sets:
            raise Exception(f"AnnotationSet with name {name} does not exist")
        del self._annotation_sets[name]
        if self._changelog:
            self._changelog.append({"command": "annotations:remove", "set": name})

    def __repr__(self) -> str:
        """
        String representation of the document, showing all content.

        :return: string representation
        """
        return "Document({},features={},anns={})".format(
            self.text, self._features, self._annotation_sets.__repr__()
        )

    def __str__(self) -> str:
        asets = (
            "["
            + ",".join([f"'{k}':{len(v)}" for k, v in self._annotation_sets.items()])
            + "]"
        )
        return "Document({},features={},anns={})".format(
            self.text, self._features, asets
        )

    def to_dict(self, offset_type=None, annsets=None, **kwargs):
        """Convert this instance to a dictionary that can be used to re-create the instance with
        from_dict.
        NOTE: if there is an active changelog, it is not included in the output as this
        field is considered a transient field!

        Args:
          offset_type: convert to the given offset type on the fly (Default value = None)
          annsets: if not None, a list of annotation set/type specifications: each element
              is either a string, the name of the annotation set to include, or a tuple where the
              first element is the annotation set name and the second element is either a
              type name or a list of type names. The same annotation set name should not be used
              in more than one specification.
          **kwargs: get passed on to the to_dict methods of included objects.

        Returns:
          the dictionary representation of this instance

        """
        # if the specified offset type is equal to what we have, do nothing, otherwise
        # create an offset mapper and pass it down to where we actually convert the annotations

        if offset_type is not None:
            assert offset_type == OFFSET_TYPE_JAVA or offset_type == OFFSET_TYPE_PYTHON
            if offset_type != self.offset_type:
                if self._text is not None:
                    om = OffsetMapper(self._text)
                    kwargs["offset_mapper"] = om
                    kwargs["offset_type"] = offset_type
        else:
            offset_type = self.offset_type

        # create the annotation sets map
        if annsets is not None:
            annsets_dict = {}
            for spec in annsets:
                if isinstance(spec, str):
                    tmpset = self._annotation_sets.get(spec)
                    if tmpset is not None:
                        annsets_dict[spec] = tmpset.to_dict(**kwargs)
                else:
                    setname, types = spec
                    if isinstance(types, str):
                        types = [types]
                    tmpset = self._annotation_sets.get(setname)
                    if tmpset is not None:
                        annsets_dict[setname] = self._annotation_sets[setname].to_dict(
                            anntypes=types, **kwargs
                        )
        else:
            annsets_dict = {
                name: aset.to_dict(**kwargs)
                for name, aset in self._annotation_sets.items()
            }

        return {
            "annotation_sets": annsets_dict,
            "text": self._text,
            "features": self._features.to_dict(),
            "offset_type": offset_type,
            "name": self.name,
        }

    @staticmethod
    def from_dict(dictrepr, **kwargs):
        """Return a Document instance as represented by the dictionary dictrepr.

        Args:
          dictrepr: return: the initialized Document instance
          **kwargs:

        Returns:
          the initialized Document instance

        """
        feats = dictrepr.get("features")
        doc = Document(dictrepr.get("text"), features=feats)
        doc.name = dictrepr.get("name")
        doc.offset_type = dictrepr.get("offset_type")
        if (
            doc.offset_type != OFFSET_TYPE_JAVA
            and doc.offset_type != OFFSET_TYPE_PYTHON
        ):
            raise Exception("Invalid offset type, cannot load: ", doc.offset_type)
        annsets = {
            name: AnnotationSet.from_dict(adict, owner_doc=doc)
            for name, adict in dictrepr.get("annotation_sets").items()
        }
        doc._annotation_sets = annsets
        return doc

    def save(
        self,
        destination,
        fmt=None,
        offset_type=None,
        mod="gatenlp.serialization.default",
        annsets=None,
        **kwargs,
    ):
        """Save the document to the destination file.

        Args:
            destination: either a file name or something that has a write(string) method.
            fmt: serialization format, by default the format is inferred from the file extension.
            offset_type: store using the given offset type or keep the current if None
                (Default value = None)
            mod: module where the document saver is implemented.
                (Default value = "gatenlp.serialization.default")
            annsets: if not None, a list of annotation set names or tuples of set name and a
                list of annotation types to include in the serialized document.
            kwargs: additional parameters for the document saver.
        """
        if annsets is not None:
            kwargs["annsets"] = annsets
        if fmt is None or isinstance(fmt, str):
            m = importlib.import_module(mod)
            saver = m.get_document_saver(destination, fmt)
            saver(Document, self, to_ext=destination, offset_type=offset_type, **kwargs)
        else:
            # assume fmt is a callable to get used directly
            fmt(Document, self, to_ext=destination, offset_type=offset_type, **kwargs)

    def save_mem(
        self,
        fmt="json",
        offset_type=None,
        mod="gatenlp.serialization.default",
        **kwargs,
    ):
        """Serialize to a string or bytes in the given format.

        Args:
            fmt: serialization format to use. (Default value = "json")
            offset_type: store using the given offset type or keep the current if None
                (Default value = None)
            mod: module where the document saver is implemented.
                (Default value = "gatenlp.serialization.default")
            kwargs: additional parameters for the format.
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
        Load or import a document from the given source. The source can be a file path or
        file name or a URL. If the type of the source is str, then if it starts with
        "http[s]://" it will get treated as a URL. In order to deliberatly use a file instead of
        a URL, create a pathlib Path, in order to deliberately use URL instead of a file parse
        the URL using urllib.

        Example: `Document.load(urllib.parse.urlparse(someurl), fmt=theformat)`

        Example: `Document.load(pathlib.Path(somepath), fmt=theformat)`

        NOTE: the offset type of the document is always converted to PYTHON when loading!

        Args:
            source: the URL or file path to load from.
            fmt: the format of the source. By default the format is inferred by the file extension.
                The format can be a format memnonic like "json", "html", or a known mime type
                like "text/bdocjs".
          mod: the name of a module where the document loader is implemented.
              (Default value = "gatenlp.serialization.default")
          kwargs: additional format specific keyword arguments to pass to the loader

        Returns:
          the loaded document
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

        Args:
            source: the string/bytes to deserialize
            fmt: if string, the format identifier or mime type (Default value = "json"), otherwise
                assumed to be a callable that retrieves and returns the document
            mod: the name of the module where the loader is implemented
                (Default value = "gatenlp.serialization.default")
            kwargs: additional arguments to pass to the loader
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
        Creates a shallow copy except the changelog which is set to None. The document feature map is
        a new instance, so features added in one copy will not show up in the other. However if
        feature values of copied features are objects, they are shared between the copies.
        Annotation sets are separate but the features of shared annotations are shared.

        Returns:
            shallow copy of the document
        """
        doc = Document(self._text)
        doc._annotation_sets = dict()
        for name, aset in self._annotation_sets.items():
            doc._annotation_sets[name] = aset.copy()
            doc._annotation_sets[name]._owner_doc = doc
        doc.offset_type = self.offset_type
        doc._features = self._features.copy()
        return doc

    def copy(self, annsets=None):
        """
        Creates a shallow copy except the changelog which is set to None. If annsets is specified,
        creates a shallow copy but also limits the annotations to the one specified.

        Args:
          annsets: if not None, a list of annotation set/type specifications: each element
              is either a string, the name of the annotation set to include, or a tuple where the
              first element is the annotation set name and the second element is either a
              type name or a list of type names. The same annotation set name should not be used
              in more than one specification.

        Returns:
            shallow copy of the document, optionally with some annotations removed
        """
        if annsets is None:
            return self.__copy__()
        doc = Document(self._text)
        doc.offset_type = self.offset_type
        doc._features = self._features.copy()
        doc._annotation_sets = dict()
        for spec in annsets:
            if isinstance(spec, str):
                tmpset = self._annotation_sets.get(spec)
                if tmpset is not None:
                    doc._annotation_sets[spec] = self._annotation_sets[spec].copy()
                    doc._annotation_sets[spec]._owner_doc = doc
            else:
                setname, types = spec
                if isinstance(types, str):
                    types = [types]
                tmpset = self._annotation_sets.get(setname)
                if tmpset is not None:
                    annset = AnnotationSet(owner_doc=doc, name=setname)
                    anns = self.annset(setname).with_type(types)
                    for ann in anns:
                        annset.add_ann(ann)
                    doc._annotation_sets[setname] = annset
        return doc

    def deepcopy(self, annsets=None, memo=None):
        """
        Creates a deep copy, except the changelog which is set to None. If annset is not None, the
        annotations in the copy are restricted to the given set.

        Args:
            memo: the memoization dictionary to use.
            annsets: which annsets and types to include

        Returns:
            a deep copy of the document.
        """
        if self._features is not None:
            fts = lib_copy.deepcopy(self._features.to_dict(), memo)
        else:
            fts = None
        doc = Document(self._text, features=fts)
        doc._changelog = None
        doc.offset_type = self.offset_type
        if annsets is None:
            doc._annotation_sets = lib_copy.deepcopy(self._annotation_sets, memo)
        else:
            doc._annotation_sets = dict()
            for spec in annsets:
                if isinstance(spec, str):
                    tmpset = self._annotation_sets.get(spec)
                    if tmpset is not None:
                        doc._annotation_sets[spec] = lib_copy.deepcopy(tmpset, memo)
                        doc._annotation_sets[spec]._owner_doc = doc
                else:
                    setname, types = spec
                    if isinstance(types, str):
                        types = [types]
                    tmpset = self._annotation_sets.get(setname)
                    if tmpset is not None:
                        annset = AnnotationSet(owner_doc=doc, name=setname)
                        anns = tmpset.with_type(types)
                        for ann in anns:
                            annset.add_ann(lib_copy.deepcopy(ann, memo))
                        doc._annotation_sets[setname] = annset
        return doc

    def __deepcopy__(self, memo=None):
        """
        Creates a deep copy, except the changelog which is set to None.

        Args:
            memo: the memoization dictionary to use.

        Returns:
            a deep copy of the document.
        """
        return lib_copy.deepcopy(self, memo=memo)

    def _repr_html_(self):
        """
        Render function for Jupyter notebooks. Returns the html-ann-viewer HTML.
        This renders the HTML for notebook, for offline mode, but does not add the JS
        but instead initializes the JS in the notebook unless gatenlp.init_notebook()
        has bee called already.
        """
        return self._notebook_show()

    # TODO: maybe allow manual selection of how to show the document, e.g. also by
    # writing to a tmp file and browsing in a browser, or pprint etc.
    def show(self, htmlid=None, annsets=None, doc_style=None):
        """
        Show the document in a Jupyter notebook. This allows to assign a specific htmlid so
        the generated HTML can be directly styled afterwards.
        This directly sends the rendered document to the cell (no display/HTML necessary).

        Args:
            htmlid: the HTML id prefix to use for classes and element ids.
            annsets: if not None, a list of annotation set/type specifications.
                Each element is either
                the name of a set to fully include, or a tuple with the name of the set as
                the first element
                and with a single type name or a list of type names as the second element
            doc_style: if not None, use this as the style for the document text box
        """
        if in_notebook():
            self._notebook_show(htmlid=htmlid, display=True, annsets=annsets, doc_style=doc_style)
        else:
            return self.__str__()

    def _notebook_show(self, htmlid=None, display=False, annsets=None, doc_style=None):
        from gatenlp.gatenlpconfig import gatenlpconfig
        from gatenlp.serialization.default import HtmlAnnViewerSerializer
        from IPython.display import display_html

        if not gatenlpconfig.notebook_js_initialized:
            HtmlAnnViewerSerializer.init_javscript()
            gatenlpconfig.notebook_js_initialized = True
        html = self.save_mem(
            fmt="html-ann-viewer",
            notebook=True,
            add_js=False,
            offline=True,
            htmlid=htmlid,
            annsets=annsets,
            doc_style=doc_style,
        )
        if display:
            display_html(html, raw=True)
        else:
            return html

    def attach(self, annset, name, check=True):
        """
        Attach a detached set to the document. This should get used with caution and is mainly
        intended for use inside the gatenlp library to allow for fast incremental creation of
        new documents and document sets. The set can only be added if a set with the given name
        does not yet exist at all.

        Args:
            annset: the annotation set to attach
            name: the name for the annotation set
            check: if False, prevent any checking. WARNING: this may create an inconsistent/illegal document!
        """
        if name in self._annotation_sets:
            raise Exception(f"Cannot attach set, a set with the name {name} already exists")
        if check:
            # check if the offsets are consistent with the document
            l = len(self)
            for ann in annset._annotations.values():
                if ann.end > l:
                    raise Exception(f"Cannot attach set, annotation beyond text end: {ann}")
        self._annotation_sets[name] = annset
        annset._owner_doc = self


class MultiDocument(Document):
    """
    NOTE: This is just experimental for now, DO NOT USE!

    A MultiDocument can store more than one document, each identified by their ids. One of those
    documents is always the "active" one and the MultiDocument can be used just like a Document
    with that content. In addition, there are methods to make each of the other documents active
    and to create mappings between annotations of pairs of documents.

    An AnnotationMapping is something that maps annotations to annotations, either for the same
    document, from the same or different sets, of for different documents. Once an annotation
    becomes part of a mapping, that annotation is becoming immutable. Even if the original
    annotation in the document changes or gets removed, the mapping retains the original copy of
    the annotation until the mapping is modified or removed.
    """

    # TODO: ALL necessary fields of the document must be references of mutable objects so that
    # if something is changed for the active document the one stored in the documents map is
    # really updated as well, or we must override the updating method to change both!
    # A better way could be to override all methods to always directly change the document in the
    # documents map, and simply pass on all calls to the activated document.
    # In that case, to_dict and from_dict would actually generate the fields for normal document
    # readers and ignore them on restore
    def __init__(
        self, text: str = None, features=None, changelog: ChangeLog = None, docid=0
    ):
        logger.warning("Experimental feature, DO NOT USE")
        self.documents = {}  # map from document id to document
        self._mappings = None  # TODO: we need to implement this
        self._docid = None
        doc = Document(text, features=features, changelog=changelog)
        self.documents[docid] = doc
        self.activate(docid)

    @property
    def docid(self):
        return self._docid

    def activate(self, docid=0):
        if docid not in self.documents:
            raise Exception(f"Cannot activate id {docid}, not in MultiDocument")
        doc = self.documents[docid]
        self._changelog = doc._changelog
        self._features = doc._features
        self._annotation_sets = doc._annotation_sets
        self._text = doc._text
        self.offset_type = OFFSET_TYPE_PYTHON
        self._name = doc._name
        self._docid = docid

    def add_document(self, doc, docid=None, activate=False):
        if docid is None:
            docid = len(self.documents)
        elif docid in self.documents:
            raise Exception(
                f"Cannot add document to MultiDocument, id {docid} already exists"
            )
        self.documents[docid] = doc
        if activate:
            self.activate(docid)
        return docid

    def to_dict(self, offset_type=None, **kwargs):
        # TODO: check what to do with the offset type parameter!
        # The basic strategy is that we simply create the dictionary for the active document plus
        # the entries for the documents map and the annotation mappings. That way, any reader of the
        # dict representation which just ignored unknown fields can still read this in as a normal
        # document from the active document.
        # The drawback is that the active document is represented twice, but OK
        thedict = {
            "annotation_sets": {
                name: aset.to_dict() for name, aset in self._annotation_sets.items()
            },
            "text": self._text,
            "features": self._features.to_dict(),
            "offset_type": self.offset_type,
            "name": self.name,
        }
        thedict["documents"] = {
            docid: doc.to_dict() for docid, doc in self.documents.items()
        }
        thedict["docid"] = self._docid
        thedict["mappings"] = self._mappings
        return thedict

    @staticmethod
    def from_dict(dictrepr, **kwargs):
        """
        Create a MultiDocument from the dictionary representation.

        Args:
            dictrepr: the dictionary representation
            **kwargs: additional kwargs to pass on

        Returns:

        """
        feats = dictrepr.get("features")
        docid = dictrepr.get("docid")
        doc = MultiDocument(dictrepr.get("text"), features=feats, docid=docid)
        doc.name = dictrepr.get("name")
        doc.offset_type = dictrepr.get("offset_type")
        if (
            doc.offset_type != OFFSET_TYPE_JAVA
            and doc.offset_type != OFFSET_TYPE_PYTHON
        ):
            raise Exception("Invalid offset type, cannot load: ", doc.offset_type)
        annsets = {
            name: AnnotationSet.from_dict(adict, owner_doc=doc)
            for name, adict in dictrepr.get("annotation_sets").items()
        }
        doc._annotation_sets = annsets
        doc.documents = {
            did: Document.from_dict(d)
            for did, d in dictrepr.get("documents", {}).items()
        }
        # TODO: get the mappings back!
        return doc
