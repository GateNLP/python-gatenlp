"""
A "mixin" class to use for classes which should have features. This turns the class into something
that can be used much like a dict in addition to original methods of the class. The inheriting class
must implement _log_feature_change(command, feature=None, value=None) and must have an attribute
changelogger.
"""


class FeatureBearer:

    def __init__(self, initialfeatures=None):
        """
        Initialise any features, if necessary.
        :param initialfeatures: an iterable containing tuples of initial feature key/value pairs
        :return:
        """
        if initialfeatures is not None:
            self.features = dict(initialfeatures)
        else:
            self.features = None
        self.changelogger = None  # this must be set by the inheriting class!

    def _log_feature_change(self, command, feature=None, value=None):
        """
        This should be overriden by the inheriting class!
        :param command: the command to log
        :param feature: the feature name involved
        :param value: the value involved
        :return:
        """
        raise Exception("must be overridden by the inheriting class")

    def clear(self):
        """
        Remove all features.
        :return:
        """
        # if we do not have features, this is a NOOP
        if self.features is None:
            return
        self._log_feature_change("CLEAR_FEATURES")
        # instead of emptying the dict, we remove it comepletely, maybe it wont be used anyway
        self.features = None

    def pop(self, key, default=None):
        """
        Remove the given key and return its value, if not found, default is returned.
        :param key: feature to remove
        :param default: value to return if feature does not exist
        :return:
        """
        if self.features is None:
            return default
        self._log_feature_change("REMOVE_FEATURE", feature=key)
        ret = self.features.pop(key, default)
        if len(self.features) == 0:
            self.features = None
        return ret

    def __setitem__(self, key, value):
        """
        Set feature to the given value
        :param key: feature name
        :param value: value
        :return:
        """
        if self.features is None:
            self.features = dict()
        self._log_feature_change("UPDATE_FEATURE", feature=key, value=value)
        self.features[key] = value

    def __delitem__(self, featurename):
        """
        Remove the feature with that name
        :param key:
        :return:
        """
        if self.features is None:
            raise KeyError(featurename)
        self._log_feature_change("REMOVE_FEATURE", feature=featurename)
        del self.features[featurename]

    def get(self, key, default=None):
        if self.features is None:
            return default
        return self.features.get(key, default)

    def __contains__(self, key):
        if self.features is None:
            return False
        return key in self.features

    def featurenames(self):
        """
        Return an iterable with the feature names. This is NOT a view and does not update when the features change!
        :return:
        """
        if self.features is None:
            return set()
        else:
            return set(self.features.keys())

    def featurevalues(self):
        """
        Return an iterable with the feature values. This is NOT a view and does not update when the features change!
        :return:
        """
        if self.features is None:
            return []
        else:
            return [set(self.features.keys())]

    def features(self):
        """
        Return a shallow copy of the feature map. This is NOT a view and does not update when the features change!
        :return:
        """
        if self.features is None:
            return {}
        else:
            return self.features.copy()

    def update(self, *other, **kwargs):
        """
        Update the features from another map or an iterable of key value pairs or from keyword arguments
        :param other: another dictionary or an iterable of key,value pairs
        :param kwargs: used to update the features
        :return:
        """
        if self.features is None:
            self.features = {}
        if other:
            if hasattr(other, "keys"):
                for k in other:
                    self.feature[k] = other[k]
            else:
                for k, v in other:
                    self.feature[k] = v
        if kwargs:
            for k in kwargs:
                self.feature[k] = kwargs[k]


    def num_features(self):
        """
        Return the number of features. We do not use "len" for this, since the feature bearing object may
        have its own useful len implementation.
        :return: number of features
        """
        if self.features is None:
            return 0
        else:
            return len(self.features)
