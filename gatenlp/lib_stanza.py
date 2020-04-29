"""
Support for using stanford stanza (see https://stanfordnlp.github.io/stanza/):
convert from stanford Stanza output to gatenlp documents and annotations.
"""
from gatenlp import Document


def apply_stanza(nlp, gatenlpdoc, setname=""):
    """
    Run the stanford stanza pipeline on the gatenlp document and transfer the annotations.
    This modifies the gatenlp document in place.

    :param nlp: StanfordNLP pipeline
    :param gatenlpdoc: gatenlp document
    :param setname: set to use
    :return:
    """
    doc = nlp(gatenlpdoc.text)
    return stanza2gatenlp(doc, gatenlpdoc=gatenlpdoc, setname=setname)


def tok2tok(tok):
    """
    Create a copy of a Stanza token, prepared for creating an annotation: this is a dict that has
    start, end and id keys and everything else in a nested dict "fm".
    :param tok: original stanza token
    :return: what we use to create a Token annotation
    """
    newtok = {}
    newtok["id"] = tok["id"]
    fm = {}
    fm.update(tok)
    newtok["fm"] = fm
    feats = fm.get("feats")
    if feats is not None:
        del fm["feats"]
        for feat in feats.split("|"):
            k, v = feat.split("=")
            fm[k] = v
    misc = fm.get("misc")
    if misc is not None:
        del fm["misc"]
        msettings = misc.split("|")
        ostart = None
        oend = None
        othersettings = []
        for ms in msettings:
            k, v = ms.split("=")
            if k == "start_char":
                ostart = int(v)
            elif k == "end_char":
                oend = int(v)
            else:
                othersettings.append(ms)
        if ostart is not None:
            newtok["start"] = ostart
        if oend is not None:
            newtok["end"] = oend
        if othersettings:
            for os in othersettings:
                k, v = ms.split("=")
                fm[k] = v
    return newtok

def stanza2gatenlp(stanzadoc, gatenlpdoc=None,
                   setname="",
                   token_type="Token",
                   sentence_type="Sentence",
                   add_entities=True,
                   ent_prefix=None,
                   ):
    """
    Convert a Stanford Stanza document to a gatenlp document. If a gatenlp document is already
    provided, add the annotations from the Stanford Stanza document to it. In this case the
    original gatenlpdoc is used and gets modified.
    :param stanzadoc: a Stanford Stanza document
    :param gatenlpdoc: if None, a new gatenlp document is created otherwise this
    document is added to.
    :param setname: the annotation set name to which the annotations get added, empty string
    for the default annotation set.
    :param token_type: the annotation type to use for tokens, if needed
    :param sentence_type: the annotation type to use for sentence anntoations
    :param add_entities: if True, add any entities as well
    :param ent_prefix: if None, use the original entity type as annotation type, otherwise add the given string
    to the annotation type as a prefix.
    :return: the new or modified gatenlp document
    """
    if gatenlpdoc is None:
        retdoc = Document(stanzadoc.text)
    else:
        retdoc = gatenlpdoc
    toki2annid = {}
    annset = retdoc.get_annotations(setname)
    # stanford nlp processes text in sentence chunks, so we do everything per sentence
    notmatchedidx = 0
    for sent in stanzadoc.sentences:
        # go through the tokens: in stanza, each token is a list of dicts, normally there is one dict
        # which also has the offset information in "misc", but for multiword tokens, there seems to be
        # one "header" dict for the range of words which has the offset info and NER label and then
        # one additional element per word which has all the rest.
        # For our purposes we create a list of dicts where for normal tokens we just copy the element, but for
        # multiword tokens we copy over something that has fake offsets and all the features
        newtokens = []
        for t in sent.tokens:
            t = t.to_dict()
            if len(t) == 1:
                newtokens.append(tok2tok(t[0]))
            else:
                tokinfo = tok2tok(t[0])
                words = t[1:]
                fm = tokinfo.get("fm")
                ner = fm.get("ner")
                text = fm.get("text")
                start = tokinfo["start"]
                end = tokinfo["end"]
                for i, w in enumerate(words):
                    tok = tok2tok(w)
                    tok["fm"]["ner"] = ner
                    tok["fm"]["token_text"] = text
                    os = min(start + i, end-1)
                    tok["start"] = os
                    if i == len(words)-1:
                        tok["end"] = end
                    else:
                        tok["end"] = os+1
                    newtokens.append(tok)
        # now go through the new token list and create annotations
        idx2annid = {}  # map stanza word id to annotation id
        starts = []
        ends = []
        for t in newtokens:
            start = t["start"]
            end = t["end"]
            stanzaid = t["id"]
            starts.append(start)
            ends.append(end)
            annid = annset.add(start, end, token_type, t["fm"])
            idx2annid[stanzaid] = annid
        # create a sentence annotation from beginning of first word to end of last
        sentid = annset.add(starts[0], ends[-1], sentence_type)
        # now replace the head index with the corresponding annid, the head index "0" is
        # mapped to the sentence annotation
        idx2annid["0"] = sentid
        for annid in list(idx2annid.values()):
            ann = annset.get(annid)
            hd = ann.get_feature("head")
            if hd is not None:
                hd = str(hd)
                ann.set_feature("head", idx2annid[hd])

        # add the entities
        if add_entities:
            for e in stanzadoc.entities:
                if ent_prefix:
                    anntype = ent_prefix + e.type
                else:
                    anntype = e.type
                annset.add(e.start_char, e.end_char, anntype)
    return retdoc
