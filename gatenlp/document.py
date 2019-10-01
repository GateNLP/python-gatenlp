import collections

from .annotation_set import AnnotationSet
from .feature_bearer import FeatureBearer


# About offsets: the text of the document, when stored as json, is always saved encoded as utf-8, no matter
# if the document got saved from Java or from Python.
# However, the annotation offsets, if saved from Java refer to UTF16 code units, while the Python annotation offsets
# refer to unicode code points. When we load a serialised document from JSON, the annotations offsets may be
# java or python offsets. If they are python offsets, nothing needs to be done. If they are java offsets,
# we need to be able to map back to python offsets by creating the mapping from java to python offsets.
# In order to do this, we first create the python to java mapping, then invert that mapping.

class OffsetMapper:
    def __init__(self, text):
        """
        Calculate an offset mapping unicode code points to utf16 code units.
        :param text: the text as a python string
        """
        import numpy as np
        # TODO: maybe we should not create/keep the python2java?
        # for mapping from python to java we create an array with the java offset for each python character,
        # so this array has as many elements as there are characters
        cur_java_off = 0
        cur_python_off = 0
        python2java_list = [0]
        java2python_list = [0]
        for i, c in enumerate(text[:-1]):
            # get the java size of the next character
            width = int(len(c.encode("utf-16be"))/2)
            assert width == 1 or width == 2
            # the next java offset we get by incrementing the java offset by the with of the current char
            cur_java_off += width
            python2java_list.append(cur_java_off)
            # i is the current python offset, so we append this as many times to java2python_list as we have width
            java2python_list.append(i)
            if width == 2:
                java2python_list.append(i)
        self.python2java = np.array(python2java_list, np.int32)
        self.java2python = np.array(java2python_list, np.int32)

    def convert_from_java(self, *offsets):


class _AnnotationSetsDict(collections.defaultdict):
    def __init__(self, changelogger=None, owner_doc=None):
        super().__init__()
        self.changelogger = changelogger
        self.owner_doc = owner_doc

    def __missing__(self, key):
        annset = AnnotationSet(name=key, changelog=self.changelogger, owner_doc=self.owner_doc)
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
    *
    """
    def __init__(self, text, features=None, changelog=None):
        super().__init__(features)
        self.changelog = changelog
        self.annotation_sets = _AnnotationSetsDict(self.changelog, owner_doc=self)
        self._text = text

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        raise NotImplementedError("Text cannot be modified in a Python processing resource")

    def size(self):
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
        return len(self._text)

    def get_annotations(self, name=""):
        """
        Get the named annotation set, if name is not given or the empty string, the default annotation set.
        If the annotation set does not already exist, it is created.
        :return: the specified annotation set.
        """
        return self.annotation_sets[name]

    def get_annotation_set_names(self):
        """
        Return the set of known annotation set names.
        :return: annotation set names
        """
        return self.annotation_sets.keys()

    def set_source_url(self, url):
        """

        :param url:
        :return:
        """
        pass  # TODO

    def get_source_url(self):
        """

        :return:
        """
        pass  # TODO

    # TODO: all the other fields to allow round-tripping an original GATE document
