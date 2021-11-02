"""
Module that defines classes for matching annotators other than gazetteers which match e.g. regular expressions
of strings or annotations.
"""
from gatenlp import Document
from gatenlp.processing.annotator import Annotator


class StringRegexAnnotator(Annotator):
    """
    NOT YET IMPLEMENTED
    """
    def __init__(self, source=None, source_fmt="file",
                 outset_name="", out_type="Match",
                 annset_name="", containing_type=None,
                 features=None,
                 skip_longest=False,
                 match="all",
                 engine='re'
                 ):
        """
        Create a StringRegexAnnotator and optionally load regex patterns.

        Args:
            source: where to load the regex rules from, format depends on source_fmt. If None, nothing is loaded.
            source_fmt: the format of the source. Either "list" for a list of tuples, where the first element
                is a compiled regular expression and the second element is a tuple. That tuple describes the
                annotations to create for a match. The first element of the tuple is the annotation type or None
                to use the out_type. The second element is a dictionary mapping each group number of the match
                to a dictionary of features to assign. If the feature value is the string "$n" with n a group
                number, then the value for that match group is used.
                Or the source_fmt can be "file" in which case the rules are loaded from a file with that path.
            outset_name:
            out_type:
            annset_name:
            containing_type:
            features:
            skip_longest:
            match:
            engine:
        """
        pass

    def __call__(self, doc: Document, **kwargs):
        pass

# class AnnotationRegexMatcher:
#    """ """
#    pass
