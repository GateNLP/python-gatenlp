import collections

from .annotation_set import AnnotationSet


class _AnnotationSetsDict(collections.defaultdict):
    def __init__(self, changelogger=None, owner_doc=None):
        super().__init__()
        self.changelogger = changelogger
        self.owner_doc = owner_doc

    def __missing__(self, key):
        annset = AnnotationSet(name=key, changelogger=self.changelogger, owner_doc=self.owner_doc)
        self[key] = annset
        return annset


class Document(object):
    def __init__(self, text, features=None, changelogger=None):
        self.changelogger = changelogger
        self.annotation_sets = _AnnotationSetsDict(self.changelogger, owner_doc=self)
        self._text = text
        self.features = features

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        raise NotImplementedError("Text cannot be modified in a Python processing resource")

    def size(self):
        return int(len(self.text))

    def __len__(self):
        return self.size()

    def __getitem__(self, name):
        """
        Return the annotation set with the given name.
        :param name: name of the annotation set
        :return: the annotation set
        """
        return self.annotation_sets[name]

    def get_annotations(self, name=""):
        """
        Get the named annotation set, if name is not given or the empty string, the default annotation set.
        :return: the specified annotation set.
        """
        return self.annotation_sets[name]

    def get_annotation_set_names(self):
        """
        Return the set of known annotation set names.
        :return: annotation set names
        """
        return self.annotation_sets.keys()
