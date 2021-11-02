"""
Base class for all gazetteer annotators
"""
from typing import Union, List
from gatenlp import Document
from gatenlp.processing.annotator import Annotator


class GazetteerAnnotator(Annotator):
    def __call__(self, doc: Document, **kwargs) -> Union[Document, List[Document], None]:
        raise RuntimeError("Not implemented in Gazetteer base class")

class StringGazetteerAnnotator(GazetteerAnnotator):
    """
    A gazetteer annotator the can be applied to strings.
    """
    def find_all(self, text, *args, **kwargs):
        pass
