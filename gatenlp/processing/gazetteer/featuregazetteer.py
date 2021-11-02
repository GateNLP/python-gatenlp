"""
Module that implements the FeatureGazetteer which matches the value of some feature of some
annotation type against a string gazetteer and adds, removes or updates annotations if a
match does or does not occur.
"""
from gatenlp.processing.annotator import Annotator


class FeatureGazetteer(Annotator):
    def __init__(self,
                 stringgaz,
                 ann_type,
                 containing_type=None,
                 feature="",
                 annset_name="",
                 outset_name="",
                 out_type="Lookup",
                 match_at_start_only=True,
                 match_at_end_only=True,
                 processing_mode="add-features",
                 handle_multiple="first"
                 ):
        """
        Create a feature gazetteer. This gazetteer processes all annotations of some type in some
        input annotation set and tries to match the value of some feature against the given string
        gazetteer. If a match is found, the action defined through the processing_mode parameter is
        taken. If the annotation does not have the feature or no match occurs, no action is performed.
        The gazetteer uses any instance of StringGazetteer to perform the matches.

        Args:
            stringgaz:
            ann_type:
            containing_type:
            feature:
            annset_name:
            outset_name:
            out_type:
            match_at_start_only:
            match_at_end_only:
            processing_mode:
            handle_multiple:
        """
        pass

    def __call__(doc, **kwargs):
        pass