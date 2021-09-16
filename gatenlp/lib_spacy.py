"""
Support for using spacy: convert from spacy to gatenlp documents and annotations.
"""

from gatenlp import Document, AnnotationSet
from gatenlp.processing.annotator import Annotator
import spacy


class AnnSpacy(Annotator):
    """ """

    def __init__(
        self,
        pipeline=None,
        outsetname="",
        token_type="Token",
        space_token_type="SpaceToken",
        sentence_type="Sentence",
        nounchunk_type="NounChunk",
        add_tokens=True,
        # add_spacetokens=True, # not sure how to do this yet
        add_entities=True,
        add_sentences=True,
        add_nounchunks=True,
        add_deps=True,
        ent_prefix=None,
    ):
        """
        Create an annotator for running a spacy pipeline on documents.

        Args:
            pipeline: if this is specified, a pre-configured spacy pipeline (default: "en_core_web_sm"
                pipeline)
        outsetname: the annotation set name where to put the annotations
        token_type: the annotation type for the token annotations
        space_token_type: type of any space token annotations
        sentence_type: the annotation type for the sentence annotations
        nounchunk_type: annotation type for noun chunks
        add_tokens: if token annotations should be added
        add_entities: if true, add entity annotations
        add_sentences: if sentence annotations should be added
        add_nounchunks: if nounchunks should be added
        add_deps: if dependencies should be added
        ent_prefix: the prefix to add to all entity annotation types
        """
        self.outsetname = outsetname

        self.token_type = token_type
        self.sentence_type = sentence_type
        self.add_entities = add_entities
        self.ent_prefix = ent_prefix
        self.space_token_type = space_token_type
        self.nounchunk_type = nounchunk_type
        self.add_tokens = add_tokens
        self.add_sentences = add_sentences
        self.add_nounchunks = add_nounchunks
        self.add_deps = add_deps
        if pipeline:
            self.pipeline = pipeline
        else:
            self.pipeline = spacy.load("en_core_web_sm")

    def __call__(self, doc, **kwargs):
        spacy_doc = self.pipeline(doc.text)
        spacy2gatenlp(
            spacy_doc,
            doc,
            setname=self.outsetname,
            token_type=self.token_type,
            space_token_type=self.space_token_type,
            sentence_type=self.sentence_type,
            nounchunk_type=self.nounchunk_type,
            add_tokens=self.add_tokens,
            add_ents=self.add_entities,
            add_nounchunks=self.add_nounchunks,
            add_sents=self.add_sentences,
            add_dep=self.add_deps,
            ent_prefix=self.ent_prefix,
        )
        return doc


def apply_spacy(nlp, gatenlpdoc, setname="", containing_anns=None,
                component_cfg=None, retrieve_spans=None):
    """Run the spacy nlp pipeline on the gatenlp document and transfer the annotations.
    This modifies the gatenlp document in place.

    Args:
        nlp: spacy pipeline
        gatenlpdoc: gatenlp document
        setname: annotation set to receive the annotations (Default value = "")
        containing_anns: annotation set or iterable of annotations. If not None, only the text covered be each
            of the annotations is analyzed. The annotations should not overlap.
        component_cfg: the component config to use for Spacy
        retrieve_spans: if not None, a list of additional span types to retrieve from the SpaCy document

    Returns:
        The modified document.
    """
    if containing_anns:
        component_config = None
        if isinstance(containing_anns, AnnotationSet):
            annsiter = containing_anns.fast_iter()
        else:
            annsiter = containing_anns
        for ann in annsiter:
            if component_cfg:
                component_config = {component_cfg: ann.features.to_dict()}
        
            covered = gatenlpdoc[ann.start:ann.end]
            spacydoc = nlp(covered, component_cfg=component_config)
            spacy2gatenlp(spacydoc, gatenlpdoc=gatenlpdoc, setname=setname,
                          start_offset=ann.start, retrieve_spans=retrieve_spans)
            elems = dir(spacydoc._)
            for elem in elems:
                if elem not in ['get', 'set', 'has']:
                    ann.features[elem] = spacydoc._.get(elem)
        return gatenlpdoc
    else:
        spacydoc = nlp(gatenlpdoc.text)
        return spacy2gatenlp(spacydoc, gatenlpdoc=gatenlpdoc, setname=setname)


def spacy2gatenlp(
    spacydoc,
    gatenlpdoc=None,
    setname="",
    token_type="Token",
    space_token_type="SpaceToken",
    sentence_type="Sentence",
    nounchunk_type="NounChunk",
    add_tokens=True,
    # add_spacetokens=True, # not sure how to do this yet
    add_ents=True,
    add_sents=True,
    add_nounchunks=True,
    add_dep=True,
    ent_prefix=None,
    start_offset=0,
    retrieve_spans=None
):
    """Convert a spacy document to a gatenlp document. If a gatenlp document is already
    provided, add the annotations from the spacy document to it. In this case the
    original gatenlpdoc is used and gets modified.

    Args:
        spacydoc: a spacy document
        gatenlpdoc: if None, a new gatenlp document is created otherwise this
            document is added to. (Default value = None)
        setname: the annotation set name to which the annotations get added, empty string
            for the default annotation set.
        token_type: the annotation type to use for tokens (Default value = "Token")
        space_token_type: the annotation type to use for space tokens (Default value = "SpaceToken")
        sentence_type: the annotation type to use for sentence anntoations (Default value = "Sentence")
        nounchunk_type: the annotation type to use for noun chunk annotations (Default value = "NounChunk")
        add_tokens: should annotations for tokens get added? If not, dependency parser
            info cannot be added either. (Default value = True)
        add_ents: should annotations for entities get added
        add_sents: should sentence annotations get added (Default value = True)
        add_nounchunks: should noun chunk annotations get added (Default value = True)
        add_dep: should dependency parser information get added (Default value = True)
        add_ents:  (Default value = True)
        ent_prefix:  (Default value = None)
        start_offset: If a document is specified, an offset where the text starts can be defined.
            This allows a part of a document with spacy and then include the annotations back to the document,
            in the corresponding possition
        retrieve_spans: if not None, a list of additional Spacy span types to retrieve

    Returns:
      the new or modified Document
    """
    
    # add_spacetokens:  (Default value = True)
    # not sure how to do this yet

    if retrieve_spans is None:
        retrieve_spans = []
    if gatenlpdoc is None:
        retdoc = Document(spacydoc.text)
        start_offset = 0
    else:
        retdoc = gatenlpdoc
    toki2annid = {}
    annset = retdoc.annset(setname)
    for tok in spacydoc:
        from_off = tok.idx
        to_off = tok.idx + len(tok)
        # is_space = tok.is_space
        fm = {
            "_i": tok.i,
            "is_alpha": tok.is_alpha,
            "is_bracket": tok.is_bracket,
            "is_currency": tok.is_currency,
            "is_digit": tok.is_digit,
            "is_left_punct": tok.is_left_punct,
            "is_lower": tok.is_lower,
            "is_oov": tok.is_oov,
            "is_punct": tok.is_punct,
            "is_quote": tok.is_quote,
            "is_right_punct": tok.is_right_punct,
            "is_sent_start": tok.is_sent_start,
            "is_space": tok.is_space,
            "is_stop": tok.is_stop,
            "is_title": tok.is_title,
            "is_upper": tok.is_upper,
            "lang": tok.lang_,
            "lemma": tok.lemma_,
            "like_email": tok.like_email,
            "like_num": tok.like_num,
            "like_url": tok.like_url,
            "orth": tok.orth,
            "pos": tok.pos_,
            "prefix": tok.prefix_,
            "prob": tok.prob,
            "rank": tok.rank,
            "sentiment": tok.sentiment,
            "tag": tok.tag_,
            "shape": tok.shape_,
            "suffix": tok.suffix_,
        }
        if spacydoc.has_annotation("ENT_IOB") and add_ents:
            fm["ent_type"] = tok.ent_type_
        if spacydoc.has_annotation("DEP") and add_dep:
            fm["dep"] = tok.dep_
        if tok.is_space:
            anntype = space_token_type
        else:
            anntype = token_type
        annid = annset.add(from_off+start_offset, to_off+start_offset, anntype, fm).id
        toki2annid[tok.i] = annid
        # print("Added annotation with id: {} for token {}".format(annid, tok.i))
        ws = tok.whitespace_
        if len(ws) > 0:
            annset.add(to_off+start_offset, to_off + len(ws)+start_offset, space_token_type, {"is_space": True})
    # if we have a dependency parse, now also add the parse edges
    if spacydoc.has_annotation("DEP") and add_tokens and add_dep:
        for tok in spacydoc:
            ann = annset.get(toki2annid[tok.i])
            ann.features["head"] = toki2annid[tok.head.i]
            ann.features["left_edge"] = toki2annid[tok.left_edge.i]
            ann.features["right_edge"] = toki2annid[tok.right_edge.i]
    if spacydoc.ents and add_ents:
        for ent in spacydoc.ents:
            if ent_prefix:
                entname = ent_prefix + ent.label_
            else:
                entname = ent.label_
            annset.add(ent.start_char+start_offset, ent.end_char+start_offset, entname, {"lemma": ent.lemma_})
    if spacydoc.sents and add_sents:
        for sent in spacydoc.sents:
            annset.add(sent.start_char+start_offset, sent.end_char+start_offset, sentence_type, {})
    if spacydoc.noun_chunks and add_nounchunks:
        for chunk in spacydoc.noun_chunks:
            annset.add(chunk.start_char+start_offset, chunk.end_char+start_offset, nounchunk_type, {})
    for spanType in retrieve_spans:
        for span in spacydoc.spans[spanType]:
            annset.add(span.start_char+start_offset, span.end_char+start_offset, spanType, {})
    return retdoc
