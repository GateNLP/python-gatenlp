"""Convert between gatenlp and spacy documents and annotations."""

from gatenlp import interact, GateNlpPr, Document


def apply_nlp(nlp, gatenlpdoc, setname=""):
    """
    Run the spacy nlp pipeline on the gatenlp document and transfer the annotations.
    This modifies the gatenlp document in place.

    :param nlp: spacy pipeline
    :param gatenlpdoc: gatenlp document
    :param setname: set to use
    :return: 
    """
    spacydoc = nlp(gatenlpdoc.text)
    return spacy2gatenlp(spacydoc, gatenlpdoc=gatenlpdoc, setname=setname)


def spacy2gatenlp(spacydoc, gatenlpdoc=None, setname="", token_type="Token",
                  spacetoken_type="SpaceToken", sentence_type="Sentence",
                  nounchunk_type="NounChunk",
                  add_tokens=True, add_spacetokens=True,
                  add_ents=True, add_sents=True, add_nounchunks=True, add_dep=True):
    """
    Convert a spacy document to a gatenlp document. If a gatenlp document is already
    provided, add the annotations from the spacy document to it. In this case the
    original gatenlpdoc is used and gets modified.
    :param spacydoc: a spacy document
    :param gatenlpdoc: if None, a new gatenlp document is created otherwise this
    document is added to.
    :param setname: the annotation set name to which the annotations get added, empty string
    for the default annotation set.
    :param token_type: the annotation type to use for tokens
    :param spacetoken_type: the annotation type to use for space tokens
    :param sentence_type: the annotation type to use for sentence anntoations
    :param nounchunk_type: the annotation type to use for noun chunk annotations
    :param add_tokens: should annotations for tokens get added? If not, dependency parser
    info cannot be added either.
    :param add_spacetokens: should annotations for space tokens get added
    :param add_ents: should annotations for entities get added
    :param add_sents: should sentence annotations get added
    :param add_nounchunks: should noun chunk annotations get added
    :param add_dep: should dependency parser information get added
    :return: the new or modified
    """
    if gatenlpdoc is None:
        retdoc = Document(spacydoc.text)
    else:
        retdoc = gatenlpdoc
    toki2annid = {}
    annset = retdoc.get_annotations(setname)
    for tok in spacydoc:
        from_off = tok.idx
        to_off = tok.idx + len(tok)
        is_space = tok.is_space
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
        if spacydoc.is_nered and add_ents:
            fm["ent_type"] = tok.ent_type_
        if spacydoc.is_parsed and add_dep:
            fm["dep"] = tok.dep_
        if tok.is_space:
            anntype = spacetoken_type
        else:
            anntype = token_type
        annid = annset.add(from_off, to_off, anntype, fm)
        toki2annid[tok.i] = annid
        # print("Added annotation with id: {} for token {}".format(annid, tok.i))
        ws = tok.whitespace_
        if len(ws) > 0:
            annset.add(to_off, to_off+len(ws), spacetoken_type, {"is_space": True})
    # if we have a dependency parse, now also add the parse edges
    if spacydoc.is_parsed and add_tokens and add_dep:
        for tok in spacydoc:
            ann = annset.get(toki2annid[tok.i])
            ann.set_feature("head", toki2annid[tok.head.i])
            ann.set_feature("left_edge", toki2annid[tok.left_edge.i])
            ann.set_feature("right_edge", toki2annid[tok.right_edge.i])
    if spacydoc.ents and add_ents:
        for ent in spacydoc.ents:
            annset.add(ent.start_char, ent.end_char, ent.label_, {"lemma": ent.lemma_})
    if spacydoc.sents and add_sents:
        for sent in spacydoc.sents:
            annset.add(sent.start_char, sent.end_char, sentence_type, {})
    if spacydoc.noun_chunks and add_nounchunks:
        for chunk in spacydoc.noun_chunks:
            annset.add(chunk.start_char, chunk.end_char, nounchunk_type, {})
    return retdoc

