"""
A map from string to some value that should be serialisable as JSON.
The map can optionally track changes through a changelogger.
"""


class FeatureMap(dict):

    def __init__(self, changelogger=None, initialfeatures=[], owner_set=None, owner_id=None):
        """
        Create a feature map, optionally so that it logs chages to the changelogger.
        If a changelogger is given, the owner should be set so it uniquely identifies
        the object that contains or references the feature map.
        (The owner should get set automatically whenever an owning object creates its FeatureMap)
        :param initialfeatures: an iterable containing tuples of initial feature key/value pairs
        :param changelogger: a ChangeLogger for tracking changes to the feature map
        :param owner_set: if the featuremap belongs to an annotation the annotation set name, if it belongs to the
        document, None.
        :param owner_id: if the featuremap belongs to an annotation, the annotation id, if it belongs to the document,
        None.
        """
        super().__init__(initialfeatures)
        self.changelogger = changelogger
        if (owner_set is None and owner_id is None) or (isinstance(owner_set, str) and isinstance(owner_id, int)):
            pass # fine, thats what we want!
        else:
            raise Exception("FeatureMap owner_set must be str and owner_id must be int, or both must be None")
        self.owner_set = owner_set
        self.owner_id = owner_id

    def _log_change(self, command, feature=None, value=None):
        if self.changelogger is None:
            return
        if self.owner_set is None:
            ch = {"command": command}
        else:
            ch = {"command": command, "annotation_set": self.owner_set, "annotation_id": self.owner_id}
        if feature is not None:
            ch[feature] = value
        self.changelogger.append(ch)

    def clear(self):
        """
        Remove all features.
        :return:
        """
        self._log_change("CLEAR_FEATURES")
        super().clear()

    def pop(self, key, default=None):
        """
        Remove the given key and return its value, if not found, default is returned.
        :param key: feature to remove
        :param default: value to return if feature does not exist
        :return:
        """
        self._log_change("REMOVE_FEATURE", feature=key)
        return super().pop(key, default)

    def __setitem__(self, key, value):
        self._log_change("UPDATE_FEATURE", feature=key, value=value)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self.log_change("REMOVE_FEATURE", feature=key)
        super().__delitem__(key)

