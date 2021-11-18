"""
Base class for all gazetteer annotators
"""
from typing import Union, List, Set
from recordclass import structclass
from gatenlp import Document
from gatenlp.processing.annotator import Annotator


class GazetteerBase(Annotator):
    def __call__(self, doc: Document, **kwargs) -> Union[Document, List[Document], None]:
        raise RuntimeError("Not implemented in Gazetteer base class")

Match = structclass(
    # A description of a match.
    # Fields:
    # start: the offset or index (in case matching a token list) where the match starts
    # end: the offset or index one past where the match ends
    # match: the matched string
    # features: the features as merged from the match rule/entry and the list features
    # type : the type as specified in the rule
    "Match", ("start", "end", "match", "features", "type")
)
