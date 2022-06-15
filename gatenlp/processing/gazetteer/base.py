"""
Base class for all gazetteer annotators
"""
from typing import Union, List, Set
from dataclasses import dataclass
from gatenlp import Document
from gatenlp.processing.annotator import Annotator


class GazetteerBase(Annotator):
    """
    Gazetteer base class.
    """
    def __call__(self, doc: Document, **kwargs) -> Union[Document, List[Document], None]:
        raise RuntimeError("Not implemented in Gazetteer base class")

# NOTE: slots=True is supported from 3.10 only
@dataclass()
class GazetteerMatch:
    """
    A description of a match.
    """
    start: int
    end: int
    match: str
    features: dict
    type: str
