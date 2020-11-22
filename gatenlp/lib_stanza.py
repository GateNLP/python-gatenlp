"""
Support for using stanford stanza (see https://stanfordnlp.github.io/stanza/):
convert from stanford Stanza output to gatenlp documents and annotations.
"""
from gatenlp import Document
from gatenlp import logger
from gatenlp.processing.annotator import Annotator
import stanza


class AnnStanza(Annotator):
    """ """

    def __init__(
        self,
        pipeline=None,
        outsetname="",
        token_type="Token",
        sentence_type="Sentence",
        add_entities=True,
        ent_prefix=None,
        **kwargs,
    ):
        """
        Create a processing resources for running a stanza pipeline on documents.

        :param pipeline: if this is specified, use a pre-configured pipeline
        :param outsetname: the annotation set name where to put the annotations
        :param token_type: the annotation type for the token annotations
        :param sentence_type: the annotation type for the sentence annotations
        :param add_entities: if true, add entity annotations
        :param ent_prefix: the prefix to add to all entity annotation types
        :param kwargs: if no preconfigured pipeline is specified, pass these arguments to
           the stanza.Pipeline() constructor see https://stanfordnlp.github.io/stanza/pipeline.html#pipeline
        """
        self.outsetname = outsetname
        self.token_type = token_type
        self.sentence_type = sentence_type
        self.add_entities = add_entities
        self.ent_prefix = ent_prefix
        [
            kwargs.pop(a, None)
            for a in ["token_type", "sentence_type", "add_entities", "ent_prefix"]
        ]
        if pipeline:
            self.pipeline = pipeline
        else:
            self.pipeline = stanza.Pipeline(**kwargs)

    def __call__(self, doc, **kwargs):
        stanza_doc = self.pipeline(doc.text)
        stanza2gatenlp(
            stanza_doc,
            doc,
            setname=self.outsetname,
            token_type=self.token_type,
            sentence_type=self.sentence_type,
            add_entities=self.add_entities,
            ent_prefix=self.ent_prefix,
        )
        return doc


def apply_stanza(nlp, gatenlpdoc, setname=""):
    """Run the stanford stanza pipeline on the gatenlp document and transfer the annotations.
    This modifies the gatenlp document in place.

    Args:
      nlp: StanfordNLP pipeline
      gatenlpdoc: gatenlp document
      setname: set to use (Default value = "")

    Returns:

    """
    doc = nlp(gatenlpdoc.text)
    return stanza2gatenlp(doc, gatenlpdoc=gatenlpdoc, setname=setname)


def tok2tok(tok):
    """Create a copy of a Stanza token, prepared for creating an annotation: this is a dict that has
    start, end and id keys and everything else in a nested dict "fm".

    Args:
      tok: original stanza token

    Returns:
      what we use to create a Token annotation

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


def stanza2gatenlp(
    stanzadoc,
    gatenlpdoc=None,
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

    Args:
      stanzadoc: a Stanford Stanza document
      gatenlpdoc: if None, a new gatenlp document is created otherwise this
         document is added to. (Default value = None)
      setname: the annotation set name to which the annotations get added, empty string
         for the default annotation set.
      token_type: the annotation type to use for tokens, if needed (Default value = "Token")
      sentence_type: the annotation type to use for sentence anntoations (Default value = "Sentence")
      add_entities: if True, add any entities as well (Default value = True)
      ent_prefix: if None, use the original entity type as annotation type, otherwise add the given string
    to the annotation type as a prefix. (Default value = None)

    Returns:
      the new or modified gatenlp document

    """
    if gatenlpdoc is None:
        retdoc = Document(stanzadoc.text)
    else:
        retdoc = gatenlpdoc
    toki2annid = {}
    annset = retdoc.annset(setname)
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
                    os = min(start + i, end - 1)
                    tok["start"] = os
                    if i == len(words) - 1:
                        tok["end"] = end
                    else:
                        tok["end"] = os + 1
                    newtokens.append(tok)
        # print(f"\n!!!!!!DEBUG: newtokens={newtokens}")
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
            annid = annset.add(start, end, token_type, features=t["fm"]).id
            idx2annid[str(stanzaid)] = annid
        # print(f"\n!!!!!!DEBUG: idx2annid={idx2annid}")
        # create a sentence annotation from beginning of first word to end of last
        sentid = annset.add(starts[0], ends[-1], sentence_type).id
        # now replace the head index with the corresponding annid, the head index "0" is
        # mapped to the sentence annotation
        idx2annid["0"] = sentid
        for annid in list(idx2annid.values()):
            ann = annset.get(annid)
            hd = ann.features.get("head")
            if hd is not None:
                hd = str(hd)
                headId = idx2annid.get(hd)
                if headId is None:
                    logger.error(
                        f"Could not find head id: {hd} for {ann} in document {gatenlpdoc.name}"
                    )
                else:
                    ann.features["head"] = idx2annid[hd]

    # add the entities
    if add_entities:
        for e in stanzadoc.entities:
            if ent_prefix:
                anntype = ent_prefix + e.type
            else:
                anntype = e.type
            annset.add(e.start_char, e.end_char, anntype)
    return retdoc
