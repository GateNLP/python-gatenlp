"""
A "mixin" class to use for classes which should have features. This turns the class into something
that can be used much like a dict in addition to original methods of the class. The inheriting class
must implement _log_feature_change(command, feature=None, value=None) and must have an attribute
changelog.
"""

from typing import List, Union, Dict, Set, KeysView


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
        self.changelog = None  # this must be set by the inheriting class!

    def _log_feature_change(self, command: str,
                            feature: Union[str, None] = None, value: Union[str, None] = None):
        """
        This should be overriden by the inheriting class!
        :param command: the command to log
        :param feature: the feature name involved. If the command is any that needds a feature name,
        the invoking method needs to make sure that the feature name is not None and also otherwise
        something that is allowed as a key.
        :param value: the value involved. None is a proper value if the feature is set. Otherwise, the value
        is always ignored.
        :return:
        """
        raise Exception("must be overridden by the inheriting class")

    def clear_features(self) -> None:
        """
        Remove all features.
        :return:
        """
        # if we do not have features, this is a NOOP
        if self.features is None:
            return
        self._log_feature_change("features:clear")
        # instead of emptying the dict, we remove it comepletely, maybe it wont be used anyway
        self.features = None

    def set_feature(self, key: str, value) -> None:
        """
        Set feature to the given value
        :param key: feature name
        :param value: value
        :return:
        """
        if self.features is None:
            self.features = dict()
        if key is None or not isinstance(key, str):
            raise Exception("A feature name must be a string, not {}".format(type(key)))
        self._log_feature_change("feature:set", feature=key, value=value)
        self.features[key] = value

    def del_feature(self, featurename: str) -> None:
        """
        Remove the feature with that name
        :param featurename: the feature to remove from the set
        :return:
        """
        if self.features is None:
            raise KeyError(featurename)
        self._log_feature_change("feature:remove", feature=featurename)
        del self.features[featurename]

    def get_feature(self, key: str, default=None):
        if self.features is None:
            return default
        return self.features.get(key, default)

    def has_feature(self, key: str) -> bool:
        if self.features is None:
            return False
        return key in self.features

    def feature_names(self) -> Union[Set, KeysView]:
        """
        Return an iterable with the feature names. This is NOT a view and does not update when the features change!
        :return:
        """
        if self.features is None:
            return set()
        else:
            return set(self.features.keys())

    def feature_values(self) -> List:
        """
        Return an iterable with the feature values. This is NOT a view and does not update when the features change!
        :return:
        """
        if self.features is None:
            return []
        else:
            return [set(self.features.values())]

    def features(self) -> Dict:
        """
        Return a shallow copy of the feature map. This is NOT a view and does not update when the features change!
        :return:
        """
        if self.features is None:
            return {}
        else:
            return self.features.copy()

    def update_features(self, *other, **kwargs):
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
                    self.set_feature(k, other[k])
            else:
                for k, v in other:
                    self.set_feature(k, v)
        if kwargs:
            for k in kwargs:
                self.set_feature(k, kwargs[k])

    def num_features(self) -> int:
        """
        Return the number of features. We do not use "len" for this, since the feature bearing object may
        have its own useful len implementation.
        :return: number of features
        """
        if self.features is None:
            return 0
        else:
            return len(self.features)
