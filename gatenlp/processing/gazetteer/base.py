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


class StringGazetteerBase(GazetteerBase):
    """
    A gazetteer annotator the can be applied to strings.
    """
    def find_all(self, text: str,
                 longest_only: Union[None, bool] = None,
                 skip_longest: Union[None, bool] = None,
                 start_offsets: Union[List, Set, None] = None,
                 end_offsets: Union[List, Set, None] = None,
                 ws_offsets: Union[List, Set, None] = None,
                 split_offsets: Union[List, Set, None] = None,):
        pass


Match = structclass(
    # TODO: why do we need features and types to be lists? Can we not generate separate Match instances
    #   for each of those, with the same offsets?????
    # A description of a match. Each match can correspond to one or more data entries. For each data entry,
    # there is a features dict and a type name.
    # Fields:
    # start: the offset or index (in case matching a token list) where the match starts
    # end: the offset or index one past where the match ends
    # match: the matched string or tokenlist
    # features: a list of feature dicts
    # types: a list of type names
    # the features and types list always have the same length, contain at least one element and 
    # elements with the same index correspond to each other.
    "Match", ("start", "end", "match", "features", "types")
)
