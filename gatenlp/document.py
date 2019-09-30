import collections

from .annotation_set import AnnotationSet
from .feature_bearer import FeatureBearer


class _AnnotationSetsDict(collections.defaultdict):
    def __init__(self, changelogger=None, owner_doc=None):
        super().__init__()
        self.changelogger = changelogger
        self.owner_doc = owner_doc

    def __missing__(self, key):
        annset = AnnotationSet(name=key, changelogger=self.changelogger, owner_doc=self.owner_doc)
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
    def __init__(self, text, features=None, changelogger=None):
        super().__init__(features)
        self.changelogger = changelogger
        self.annotation_sets = _AnnotationSetsDict(self.changelogger, owner_doc=self)
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
        if self.changelogger is None:
            return
        ch = {"command": command}
        if feature is not None:
            ch["name"] = feature
            ch["value"] = value
        self.changelogger.append(ch)

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
