"""
Support for using stanfordnlp: convert from stanfordnlp output to gatenlp documents and annotations.
"""
from gatenlp import Document
from gatenlp import utils


def apply_stanfordnlp(nlp, gatenlpdoc, setname=""):
    """Run the stanford nlp pipeline on the gatenlp document and transfer the annotations.
    This modifies the gatenlp document in place.

    Args:
      nlp: StanfordNLP pipeline
      gatenlpdoc: gatenlp document
      setname: set to use (Default value = "")

    Returns:

    """
    doc = nlp(gatenlpdoc.text)
    return stanfordnlp2gatenlp(doc, gatenlpdoc=gatenlpdoc, setname=setname)


def stanfordnlp2gatenlp(
    stanfordnlpdoc,
    gatenlpdoc=None,
    setname="",
    word_type="Word",
    sentence_type="Sentence",
):
    """Convert a StanfordNLP document to a gatenlp document. If a gatenlp document is already
    provided, add the annotations from the StanfordNLP document to it. In this case the
    original gatenlpdoc is used and gets modified.

    Args:
      stanfordnlpdoc: a StanfordNLP document
      gatenlpdoc: if None, a new gatenlp document is created otherwise this
    document is added to. (Default value = None)
      setname: the annotation set name to which the annotations get added, empty string
    for the default annotation set.
      token_type: the annotation type to use for tokens
      sentence_type: the annotation type to use for sentence anntoations (Default value = "Sentence")
      word_type:  (Default value = "Word")

    Returns:
      the new or modified

    """
    if gatenlpdoc is None:
        retdoc = Document(stanfordnlpdoc.text)
    else:
        retdoc = gatenlpdoc
    toki2annid = {}
    annset = retdoc.annset(setname)
    # stanford nlp processes text in sentence chunks, so we do everything per sentence
    # NOTE: the stanford elements do not contain any text offsets, so we have to match and find
    # them ourselves. for this we keep an index to first character in the text which has not
    # been matched yet
    notmatchedidx = 0
    for sent in stanfordnlpdoc.sentences:
        # a sentence is a list of tokens and a list of words. Some tokens consist of several words.
        # dependency parsers are over words, so we create Word and Token annotations, but we only
        # set the features per Word annotation for now.
        offsetinfos = utils.match_substrings(
            stanfordnlpdoc.text[notmatchedidx:], sent.words, getstr=lambda x: x.text
        )
        idx2annid = {}
        for oinfo in offsetinfos:
            word = oinfo[2]
            fm = {
                "string": word.text,
                "lemma": word.lemma,
                "upos": word.upos,
                "xpos": word.xpos,
                "dependency_relation": word.dependency_relation,
                "governor": int(word.governor),
            }
            for feat in word.feats.split("|"):
                if feat and feat != "_":
                    k, v = feat.split("=")
                    # TODO: maybe try to detect and convert bool/int values
                    fm["feat_" + k] = v
            snlp_idx = int(word.index)
            annid = annset.add(
                oinfo[0] + notmatchedidx, oinfo[1] + notmatchedidx, word_type, fm
            ).id
            idx2annid[snlp_idx] = annid
        # create a sentence annotation from beginning of first word to end of last
        sentid = annset.add(
            offsetinfos[0][0] + notmatchedidx,
            offsetinfos[-1][1] + notmatchedidx,
            sentence_type,
        ).id
        # now replace the governor index with the corresponding annid, the governor index is
        # mapped to the sentence annotation
        idx2annid[0] = sentid
        for annid in list(idx2annid.values()):
            ann = annset.get(annid)
            gov = ann.features.get("governor")
            if gov is not None:
                ann.features["governor"] = idx2annid[gov]
        notmatchedidx = offsetinfos[-1][1] + notmatchedidx + 1
    return retdoc
