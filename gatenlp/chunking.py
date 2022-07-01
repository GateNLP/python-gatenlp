"""
Module for chunking-related methods and annotators.
"""
import re
from typing import Union, List, Optional, Dict, Generator, Tuple
import iobes
from gatenlp import Document, Span, AnnotationSet

SPANENCS = dict(
    BIO=iobes.SpanEncoding.BIO,
    IOB=iobes.SpanEncoding.IOB,
    IOBES=iobes.SpanEncoding.IOBES,
    BILOU=iobes.SpanEncoding.BILOU,
    BMEOW=iobes.SpanEncoding.BMEOW,
    BMEWO=iobes.SpanEncoding.BMEWO,
)

PAT_WS = re.compile(r"\s+")


def normalize_type(typename):
    """
    Normalize the type name so it can be used as part of an BIO-like code that is usable in a conll-like dataset:
    replace all whitespace with a hyphen.

    Args:
        typename: the chunk type name

    Returns:
        normalized chunk type name
    """
    return re.sub(PAT_WS, "-", typename)


def doc_to_ibo(
        doc: Document,
        annset_name: str = "",
        sentence_type: Optional[str] = None,
        token_type: str = "Token",
        token_feature: Optional[str] = None,
        chunk_annset_name: Optional[str] = None,
        chunk_types: Optional[List[str]] = None,
        type2code: Optional[Dict] = None,
        scheme: str = "BIO",
        return_rows:bool = True,
) -> Generator[Union[List, Tuple], None, None]:
    """
    Extract tokens and corresponding token entity codes.

    Args:
        doc: The document to process
        annset_name: name of the annotation set which contains all the types needed
        sentence_type: if None, use whole document, otherwise generate one result per sentence type annotation,
            if the sentence contains at least one token.
        token_type: type of token annotations to use
        token_feature: if not None, use the feature instead of the covered document text
        chunk_annset_name: is specified, the annotation set name to use for retrieving the chunk annotations,
            otherwise annset_name is used for the chunk annotations too.
        chunk_types: a list of annotation types which identify chunks, each chunk type is used as entity type
            Note the chunk type annotations must not overlap, but this is currently not checked, for performance
            reasons.
        type2code: an optionam dict mapping the chunk_type to the type name used in the BIO codes
        scheme: the encoding scheme to use, default is BIO, possible: IOB, BIO, IOBES, BILOU, BMEOW, BMEWO
        return_rows: if True, return a list of (tokenstring, code) tuples for each sentence, if False return two lists
            of equal length, the first with the token strings and the second with the codes

    Yields:
        either one list of (tokenstring, code) tuples per sentence found or two lists, one with the tokenstrings and
        the other with the codes.
    """
    spanenc = SPANENCS[scheme]
    if type2code is None:
        type2code = {}
    if sentence_type is None:
        spans = [Span(0, len(doc))]
    else:
        spans = [a.span for a in doc.annset(annset_name).with_type(sentence_type)]
    all_tokens = doc.annset(annset_name).with_type(token_type)
    if chunk_types is None:
        all_chunks = AnnotationSet()
    else:
        all_chunks = doc.annset(annset_name if chunk_annset_name is None else chunk_annset_name).with_type(chunk_types)
    for span in spans:
        tokens = all_tokens.within(span)
        if len(tokens) == 0:
            continue
        # map token start offsets to token indices
        start2idx = {t.start: idx for idx, t in enumerate(tokens)}
        chunks = all_chunks.within(span)
        # now we want to know which of all the tokens are covered by chunks. So for each chunk, we check
        # which tokens are contained and append an iobes Span that points to the index of the token
        iobes_spans = []
        for chunk in chunks:
            ctokens = list(tokens.within(chunk))
            start = start2idx[ctokens[0].start]
            end = start2idx[ctokens[-1].start]+1
            iobes_span = iobes.Span(
                type=type2code.get(chunk.type, normalize_type(chunk.type)),
                start=start,
                end=end,
                tokens=tuple(range(start, end))
            )
            iobes_spans.append(iobes_span)
        codes = iobes.write_tags(iobes_spans, spanenc, length=len(tokens))
        assert len(tokens) == len(codes)
        if token_feature:
            token_strings = [t.features[token_feature] for t in tokens]
        else:
            token_strings = [doc[t] for t in tokens]
        if return_rows:
            yield [(t, c) for t, c in zip(token_strings, codes)]
        else:
            yield token_strings, codes
