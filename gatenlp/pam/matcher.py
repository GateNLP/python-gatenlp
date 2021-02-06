import re

_tmp_re_pattern = re.compile("x")
CLASS_RE_PATTERN = _tmp_re_pattern.__class__
try:
    import regex

    _tmp_regex_pattern = regex.compile("x")
    CLASS_REGEX_PATTERN = _tmp_regex_pattern.__class__
except Exception as ex:
    # if the regex module is not available, make our  code still work by introducing a dummy type
    class RegexPattern:
        pass

    CLASS_REGEX_PATTERN = RegexPattern

from gatenlp.utils import init_logger

logger = init_logger(debug=True)

__pdoc__ = {
    "FeatureMatcher.__call__": True,
    "FeatureEqMatcher.__call__": True,
    "AnnMatcher.__call__": True,
}


class FeatureMatcher:
    """
    Callable that matches the given dictionary against features.

    This creates a callable that can be used to easily check if features match the
    features and feature constraint defined by the matcher. When a matcher is created,
    the argument names are used as feature names and the argument values are either
    literal values to compare with or compiled regular expressions or callables.

    A FeatureMatcher matches as soon as all specified features match, no matter if the
    features we compare with contain additional features.

    In this example, the feature matcher will check if there are two features with the
    given names and values.

    Example:
        ```python
        fmatcher1 = FeatureMatcher(feature1 = "somevalue", feature2 = 999)
        if fmatcher(ann.features):
            print("Yay, both features are in ann.features!")
        ```

    In this example `feature1` matches if it matches the regular expression, and feature2
    matches if the given callable returns true.

    Example:
        ```python
        def checksize(x):
            return 12 <= x < 33
        NAMEPATTERN = re.compile(r"[A-Z][a-z_0-9]+")
        fmatcher2 = FeatureMatcher(name = NAMEPATTERN, size = checksize)
        ```
    """

    def __init__(self, **kwargs):
        """
        Create a FeatureMatcher instance.

        Args:
            **kwargs: arbitrary key/value pairs to use for matching features.
        """
        self.fm = kwargs  # "featurematcher"

    def __call__(self, features):
        """
        Check if the passed features match the constraints for this FeatureMatcher.

        This returns true if all the constraints defined for this FeatureMatcher are satisfied,
        even if the features contain additional features not included in the constraints.

        Args:
            features: the features to check

        Returns:
            True if the feature constraints are satisfied

        """
        for fmn in self.fm.keys():  # "featurematchername"
            if fmn not in features:
                # logger.debug(f"Feature {fmn} not in features")
                return False
        for fmn, fmv in self.fm.items():  # "featurematchername"/"featurematchervalue"
            feature = features[fmn]
            if callable(fmv):
                if not fmv(feature):
                    # logger.debug(f"Callable {fmn} did not return True for {feature}")
                    return False
            elif isinstance(fmv, CLASS_RE_PATTERN) or isinstance(
                fmv, CLASS_REGEX_PATTERN
            ):
                fstr = str(feature)
                if not fmv.match(fstr):
                    return False
            else:
                fstr = str(feature)
                tmp = str(fmv)
                if tmp != fstr:
                    return False
        return True


class FeatureEqMatcher:
    """
    Callable that matches the given dictionary against features and returns True only if all features
    match and there are no additional features.

    This works like FeatureMatcher, but all the features that get checked must satisfy the constraints
    and there must be no additional features.
    """

    def __init__(self, **kwargs):
        """
        Create a FeatureEqMatcher instance.

        Args:
            **kwargs: arbitrary key/value pairs to use for matching features.
        """
        self.features = kwargs
        self._fm = FeatureMatcher(**kwargs)

    def __call__(self, features):
        """
        Check if the passed features match the constraints for this FeatureMatcher.

        This returns true if all the constraints defined for this FeatureMatcher are satisfied,
        ONLY if the features do not contain additional features not included in the constraints.

        Args:
            features: the features to check

        Returns:
            True if the feature constraints are satisfied
        """
        for f in features.keys():
            if f not in self.features:
                return False
        if not self._fm(features):
            return False
        return True


class AnnMatcher:
    """
    A callable that matches an annotation.

    This creates a callable that can be used to check if an annotation satisfies all the constraints
    defined.
    """

    def __init__(self, type=None, features=None, features_eq=None, text=None):
        """
        Create an AnnMatcher instance.

        Args:
            type: if not None, match the type. If this is a string, match the literal string, if it is
                a compiled regular expression, match that expression, if it is a callable, call it and
                use the return value.
            features: if specified, it must be a FeatureMatcher or a dictionary which is used as the kwargs  to create
                a FeatureMatcher instance for matching the features of the annotation.
            features_eq:  if specified, it must be a FeatureEqMatcher or a dictionary which is used as the kwargs
                to create a FeatureEqMatcher instance for matching the features of the annotation.
                Only one of features or features_eq should be used.
            text: if not None, match the document text covered by the annotation. For this the
                matcher must be called with the optional `doc` parameter.
        """
        self.type = type
        if features_eq is not None:
            if callable(features_eq):
                self.features_matcher = features_eq
            else:
                self.features_matcher = FeatureEqMatcher(**features_eq)
        elif features is not None:
            if callable(features):
                self.features_matcher = features
            else:
                self.features_matcher = FeatureMatcher(**features)
        else:
            self.features_matcher = None
        self.text = text

    def __call__(self, ann, doc=None):
        """
        Check if the annotation matches.

        Args:
            ann: the annotation to check
            doc: the document the annotation refers to, only needed if the matcher contains a "text"
                constraint.

        Returns:
            True if the annotation matches, False otherwise.

        """
        if self.type is not None:
            if isinstance(self.type, str):
                if self.type != ann.type:
                    return False
            elif callable(self.type):
                if not self.type(ann.type):
                    return False
            elif isinstance(self.type, CLASS_RE_PATTERN) or isinstance(
                self.type, CLASS_REGEX_PATTERN
            ):
                if not self.type.match(ann.type):
                    return False
            else:
                tmp = str(self.type)
                if tmp != self.type:
                    return False
        if self.features_matcher is not None:
            if not self.features_matcher(ann.features):
                return False
        if self.text is not None:
            if isinstance(self.text, CLASS_RE_PATTERN) or isinstance(
                self.text, CLASS_REGEX_PATTERN
            ):
                if not self.text.match(doc[ann]):
                    return False
        return True


# Helpers for the Feature and Ann matchers: these are callables which provide a simple way to match
# text case insensitive or negate matching text or features


class nocase:
    """
    A matcher for comparing text in a case insensitive way.

    This carries out the matching by using the upper-case versions of the text compared and the
    text to compare with. This makes sure that cases like German "ß" which expands to "SS" are
    handled correctly (while uppercase "SS" often should NOT get converted to lowercase "ß").

    Example:
        ```python
        m1 = nocase("sometext")
        assert m1("SomeText")
        assert m1("SOMETEXT")
        ```
    """

    def __init__(self, text):
        """
        Create a case insensitive text matcher.

        Args:
            text: the text to match against.
        """
        self.text = text.upper()

    def __call__(self, text):
        """
        Check if the text matches.

        Args:
            text: the text to check

        Returns:
            True if the text matches
        """
        return text.upper() == self.text


class ifnot:
    """
    A matcher that returns the negation of another matcher.

    Example:
        ```python
        m1 = FeatureMatcher(f1="x", f2=22)
        m2 = ifnot(m1)  # m2 matches for features which do not contain f1="x" and not f2=22
        ```
    """

    def __init__(self, other):
        self.other = other

    def __call__(self, *args, **kwargs):
        return not self.other(*args, **kwargs)
