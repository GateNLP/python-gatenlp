"""
Google NLP client.
"""
import json
from typing import Union, Optional, List
import logging

from google.cloud import language_v1

from gatenlp.features import Features
from gatenlp.processing.annotator import Annotator
from gatenlp.utils import init_logger

# See:
# https://googleapis.dev/python/language/latest/usage.html
# https://cloud.google.com/natural-language/docs/quickstart?hl=en_GB
# https://github.com/googleapis/python-language/tree/main/samples
# https://cloud.google.com/natural-language/docs/samples
# https://cloud.google.com/natural-language/docs/reference/libraries


def set_if_not_none(thedict, thekey, thevalue, suf=None):
    """
    Helper function to set the key of a dict to the given value, if the value is not None and not something
    ending in _UNKNOWN (if it is a string)
    """
    if thevalue is not None:
        if suf:
            if isinstance(thevalue, str) and thevalue.endswith(suf):
                return
        thedict[thekey] = thevalue


class GoogleNlpAnnotator(Annotator):

    def __init__(
        self,
        which_features: Optional[Union[str, List[str]]] = None,
        lang: Optional[str] = None,
        outset_name: str = "",
        debug: bool = False,
    ):
        """
        Create an IbmNluAnnotator.

        Args:
            which_features: a comma separated list or a python list of features to return,
                possible values are: syntax, entities, document_sentiment, entity_sentiment, classify.
                Default is "syntax,entities"
            lang: if not None, the ISO 639-1 code of the language the text is in. If None, automatically
                determines the language and stores it as a document feature according to the doc_feature_map parameter.
                See supported: https://cloud.google.com/natural-language/docs/languages
            outset_name: the name of the annotation set where to create the annotations (default: "")
            debug: if True, enable debugging logging
        """
        self.outset_name = outset_name
        self.lang = lang
        self.debug = debug
        self.logger = init_logger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
        if which_features is None:
            which_features = "syntax,entities"
        if isinstance(which_features,str):
            which_features = [x.strip() for x in which_features.split(",")]
        else:
            which_features = [x.strip() for x in which_features]
        goo_feats = {}
        for feature in which_features:
            if feature == "syntax":
                goo_feats["extract_syntax"] = True
            elif feature == "entities":
                goo_feats["extract_entities"] = True
            elif feature == "document_sentiment":
                goo_feats["extract_document_sentiment"] = True
            elif feature == "entity_sentiment":
                goo_feats["extract_entity_sentiment"] = True
            elif feature == "classify":
                goo_feats["classify_text"] = True
            else:
                raise Exception(f"Processing feature {feature} not allowed")
        self.ibm_features = language_v1.types.language_service.AnnotateTextRequest.Features(**goo_feats)
        self.which_features = which_features
        self.client = language_v1.LanguageServiceClient()

    def __call__(self, doc, **kwargs):
        goodoc = language_v1.Document(
            content=doc.text,
            type_="PLAIN_TEXT",
            language=self.lang,
        )
        outset = doc.annset(self.outset_name)
        resp = self.client.annotate_text(document=goodoc, encoding_type="UTF32", features=self.ibm_features)
        if self.debug:
            self.logger.debug(f"Response: {resp}")
        set_if_not_none(doc.features, "language", resp.language)
        if self.ibm_features.extract_document_sentiment:
            set_if_not_none(doc.features, "document_sentiment_magnitude", resp.document_sentiment.magnitude)
            set_if_not_none(doc.features, "document_sentiment_score", resp.document_sentiment.score)
        for sentence in (resp.sentences or []):
            slen = len(sentence.text.content)
            start = sentence.text.begin_offset
            end = start + slen
            fmap = {}
            if self.ibm_features.extract_document_sentiment:
                set_if_not_none(fmap, "sentiment_magnitude", sentence.sentiment.magnitude)
                set_if_not_none(fmap, "sentiment_score", sentence.sentiment.score)
            outset.add(start, end, "Sentence", fmap)
        for token in (resp.tokens or []):
            tlen = len(token.text.content)
            start = token.text.begin_offset
            end = start + tlen
            fmap = {}
            set_if_not_none(fmap, "pos", token.part_of_speech.tag.name, suf="_UNKNOWN")
            set_if_not_none(fmap, "number", token.part_of_speech.number.name, suf="_UNKNOWN")
            set_if_not_none(fmap, "mood", token.part_of_speech.mood.name, suf="_UNKNOWN")
            set_if_not_none(fmap, "person", token.part_of_speech.person.name, suf="_UNKNOWN")
            set_if_not_none(fmap, "gender", token.part_of_speech.gender.name, suf="_UNKNOWN")
            set_if_not_none(fmap, "case", token.part_of_speech.case.name, suf="_UNKNOWN")
            set_if_not_none(fmap, "proper", token.part_of_speech.proper.name, suf="_UNKNOWN")
            set_if_not_none(fmap, "tense", token.part_of_speech.tense.name, suf="_UNKNOWN")
            set_if_not_none(fmap, "head", token.dependency_edge.head_token_index)
            set_if_not_none(fmap, "deprel", token.dependency_edge.label.name, suf="_UNKNOWN")
            set_if_not_none(fmap, "lemma", token.lemma)
            outset.add(start, end, "Token", fmap)
        for entity in (resp.entities or []):
            fmap = dict(
                type=entity.type_.name,
                salience=entity.salience,
                name=entity.name,
            )
            fmap.update(entity.metadata)
            for mention in entity.mentions:
                mlen = len(mention.text.content)
                start = mention.text.begin_offset
                end = start + mlen
                ann = outset.add(start, end, entity.type_.name, fmap)
                ann.features["mtype"] = mention.type_.name
                if self.ibm_features.extract_entity_sentiment:
                    set_if_not_none(ann.features, "sentiment_magnitude", mention.sentiment.magnitude)
                    set_if_not_none(ann.features, "sentiment_score", mention.sentiment.score)
        return doc





