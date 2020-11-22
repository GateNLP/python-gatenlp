import re

_tmp_re_pattern = re.compile("x")
CLASS_RE_PATTERN = _tmp_re_pattern.__class__
try:
    import regex

    _tmp_regex_pattern = regex.compile("x")
    CLASS_REGEX_PATTERN = _tmp_regex_pattern.__class__
except:
    # if the regex module is not available, make our  code still work by introducing a dummy type
    class RegexPattern:
        pass

    CLASS_REGEX_PATTERN = RegexPattern

from gatenlp.utils import init_logger

logger = init_logger(debug=True)


class FeatureMatcher:
    """
    Callable that matches the given dictionary against features.
    """

    def __init__(self, **kwargs):
        self.fm = kwargs  # "featurematcher"

    def __call__(self, features):
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
    """

    def __init__(self, **kwargs):
        self.features = kwargs
        self._fm = FeatureMatcher(**kwargs)

    def __call__(self, features):
        for f in features.keys():
            if f not in self.features:
                return False
        if not self._fm(features):
            return False
        return True


class AnnMatcher:
    """
    A callable that matches an ann.
    """

    def __init__(self, type=None, features=None, features_eq=None, text=None):
        self.type = type
        if features_eq is not None:
            self.features_matcher = FeatureEqMatcher(**features_eq)
        elif features is not None:
            self.features_matcher = FeatureMatcher(**features)
        else:
            self.features_matcher = None
        self.text = text

    def __call__(self, ann, doc=None):
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
    def __init__(self, text):
        self.text = text.upper()

    def __call__(self, text):
        return text.upper() == self.text


class ifnot:
    def __init__(self, other):
        self.other = other

    def __call__(self, *args, **kwargs):
        return not self.other(*args, **kwargs)
