"""
Base class for all gazetteer annotators
"""
from gatenlp.processing.annotator import Annotator


class GazetteerAnnotator(Annotator):
    def __call__(self, *args, **kwargs):
        raise RuntimeError("Not implemented in Gazetteer base class")