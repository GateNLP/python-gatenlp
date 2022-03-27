"""
Module defining several utility functions for annotating documents in various ways.
"""
from typing import List, Optional


def annotate_substrings(doc,
                        substrings: List[str],
                        outset_name: str = "",
                        featureslist: Optional[List[str]] = None,
                        ann_type: str = "Token",
                        annotate_gaps: bool = False,
                        gap_type: str = "SpaceToken",
                        raise_if_unmatched: bool = True,
                        from_offset: int = 0,
                        to_offset: Optional[int] = None
                        ):
    """
    Annotate the document by matching the text substrings in the substrings list to the corresponding locations
    in the text. If the features list is not None it must be of equal length as susbstrings and contain a dict
    of features to assign to the annotation to create. If annotate_gaps is True, the gaps between matched substrings
    will be annotated with the gap_type type.

    Args:
        doc: the document to annotate
        outset_name: the name of the output annotation set (default set)
        substrings: a list of substrings to match
        featureslist: if not None a list of dicts which are used as features for the annotations created
        ann_type: the type of the annotations created for matching substings
        annotate_gaps: if True, the gaps between matching substrings are annotated using the gap_type
        gap_type: the type to use for gap annotations
        raise_if_unmatched: if True and a substring in the substrings list cannot be matched, an exception is raised,
            otherwise, the unmatchable substring is ignored.
        from_offset: the offset where to start matching
        to_offset: the offset before which a matching substring must end (if None, the end of the document)

    Returns:
        the annotated doc, identical to the document passed
    """
    outset = doc.annset(outset_name)
    if featureslist is not None:
        assert len(featureslist) == len(substrings)
    else:
        featureslist = [{} for _ in substrings]
    if to_offset is None:
        to_offset = len(doc.text)
    assert from_offset < to_offset
    assert to_offset <= len(doc.text)
    last_end = from_offset
    for substring, features in zip(substrings, featureslist):
        idx = doc.text.find(substring, last_end, to_offset)
        if idx < 0:  # not found
            if raise_if_unmatched:
                raise Exception(f"Unmatched string '{substring}' in {doc.text} from {last_end} to {to_offset}")
        else:
            end = idx+len(substring)
            if idx > last_end and annotate_gaps:
                outset.add(last_end, idx, gap_type)
            if end <= to_offset:
                outset.add(idx, end, ann_type, features=features)
            else:
                break
    return doc
