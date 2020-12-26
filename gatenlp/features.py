"""
Module that implements class Feature for representing features.
"""
# Implementation note: Features should behave much like a dict. However, inheriting from dict
# is problematic, because dict has an odd way to implement interdependent methods, e.g. ne and eq
# are implemented separately, so the inheriting class would need to implement them separately too.
# Similar for clear and __delitem__ and other method pairs.
#
# Possible alternate approaches:
# * implement everything ourselves
# * inherit from collections.abc.MutableMapping and implement delitem, getitem, setitem, iter, len and repr
# * inherit from collections.UserDict and implement delitem, setitem and repr
#   This one IS NOT a dict but WRAPS around a dict which is accessible as self.data
# Since Features is meant to be pretty close to how a dict works and originally was implemented by
# wrapping an actual dict, the collections.UserDict approach seems to be more adequate.

from collections import UserDict
import copy as lib_copy


class Features(UserDict):
    """
    A dict-like class for storing features, which are mappings from string feature names to
    arbitrary feature values. If the Features instance is a field in another object where
    changes are getting logged in a change log, it should pass on the logger, a method for
    logging feature changes. Any copy of an instance of Features will not receive the logger,
    in order to make sure that logging happens, the instance stored in the original owning
    object must be used.
    """

    def __init__(self, *args, logger=None, **kwargs):
        """
        Initialize a Features object.

        Args:
            initialfeatures: the initial features, as for a dict.
            logger: a function for logging any changes to the feature map. This should be
                a method implemented in the owning object. It should take the following parameters:
                command, featurename, featurevalue. NOTE: this is not related to the usual logging
                from the loggin package, but for making use of tracking changes in a ChangeLog!
        """
        self._logger = logger
        if len(args) == 1:
            posarg = args[0]
            if isinstance(posarg, Features):
                super().__init__(posarg.data, **kwargs)
            else:
                super().__init__(posarg, **kwargs)
        else:
            super().__init__(**kwargs)

    def __delitem__(self, featurename):
        """
        Remove the feature with the given feature name. This raises a key error if featurename is
        not in the Features. To silently remove a key, if it exists, use `pop(fname, None)`

        Args:
            featurename: name of the feature to remove
        """
        if self._logger:
            self._logger("feature:remove", feature=featurename)
        del self.data[featurename]

    def __repr__(self):
        """
        Return string representation of the Features object.
        """
        return f"Features({self.data.__repr__()})"

    def __setitem__(self, featurename, featurevalue):
        """
        Set a feature with the given name to the given value.

        Args:
            featurename: feature name, must be string
            featurevalue:  feature value
        """
        if featurename is None or not isinstance(featurename, str):
            raise Exception(
                "A feature name must be a string, not {}".format(type(featurename))
            )
        if self._logger:
            self._logger("feature:set", feature=featurename, value=featurevalue)
        self.data[featurename] = featurevalue

    def clear(self):
        """
        Remove all features.
        """
        if self._logger:
            self._logger("features:clear")
        self.data.clear()

    def copy(self, deep=False):
        """
        Return a shallow (or deep if deep=True) copy of the features. The result is another
        instance of Features which is detached from the owner and which does not log
        the changes. However, if the copy is shallow and feature values are references
        to mutable objects, they can still get modified in the original set (without
        any logging!).

        Args:
          deep: if True return a deep instead of a shallow copy of the features. (Default value = False)

        Returns:
          a dictionary with the features
        """
        ret = Features()
        if deep:
            ret.data = deep(self.data)
        else:
            ret.data = self.data.copy()
        ret._logger = None
        return ret

    def to_dict(self, deepcopy=False, include_internal=False, memo=None):
        """
        Return a dictionary representation of the features. The returned dictionary is always a shallow
        copy of the original dictionary of features, but will be a deep copy if the parameter `deepcopy` is True.

        Note:
            Features with names that start with two underscores are considered "internal/transient" features
            and not saved. Features with names that start with one underscore are considered "internal" but
            do get saved/serialized.

        Args:
            deepcopy: if True, the dictionary is a deep copy so that mutable objects
                in the original are unaffected if they get modified in the copy. (Default value = False)
            include_internal: if True, all features, even those with names that start with double underscore ("__")
                are included in the result dictionary, these features are usually dropped.
            memo: if deepcopy is True, the memo object to use for deepcopy, if any

        Returns:
          the dict representation of the features

        """
        ret = dict()
        for k, v in self.data.items():
            if not include_internal and k.startswith("__"):
                continue
            if deepcopy:
                ret[k] = lib_copy.deepcopy(v)
            else:
                ret[k] = v
        return ret

    @staticmethod
    def from_dict(thedict, deepcopy=False, memo=None):
        """
        Create a Features instance from a dictionary. If deepcopy is True, a deepcopy is created.

        NOTE: no checks are done to make sure that feature names are string only!

        Args:
          thedict: the dictionary from which to create the Features.
          deepcopy: if True and copy is True, use a deep copy of the dictionary (Default value = False)
          memo: if deepcopy is True, the memo object to use for deepcopying

        Returns:
          the Features instance

        """
        ret = Features()
        if deepcopy:
            ret.data = lib_copy.deepcopy(thedict, memo=memo)
        else:
            ret.data = thedict.copy()
        return ret
