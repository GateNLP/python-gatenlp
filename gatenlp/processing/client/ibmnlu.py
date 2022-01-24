"""
IBM Natural Language Understanding client.
"""
import json
from typing import Union, Optional, List
import logging
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, CategoriesOptions, ConceptsOptions
from ibm_watson.natural_language_understanding_v1 import EmotionOptions, EntitiesOptions, KeywordsOptions
from ibm_watson.natural_language_understanding_v1 import RelationsOptions, SemanticRolesOptions, SentimentOptions
from ibm_watson.natural_language_understanding_v1 import SyntaxOptions, SyntaxOptionsTokens

from gatenlp.processing.annotator import Annotator
from gatenlp.utils import init_logger


def string2int(string, max=999999999, fname=""):
    """Helper function to return string converted to int or raise informative exception"""
    if string is None:
        return None
    try:
        val = int(string)
    except:
        raise Exception(f"Parameter {fname} cannot be converted to int")
    if val > max:
        raise Exception(f"Parameter {fname} exceeds maximum value {max}")
    return val


def which2ibm_features(which):
    """
    Convert the simplified list of features to an ibm features object. The which parameter is either a
    string of comma-separated feature names or a list of feature names.
    """
    if isinstance(which, str):
        which = which.split(",")
    parms = {}
    for feat in which:
        if ":" in feat:
            fname, fparm = feat.split(":", 1)
        else:
            fname, fparm = feat, None
        if fname == "syntax":
            parms["syntax"] = SyntaxOptions(tokens=SyntaxOptionsTokens(lemma=True, part_of_speech=True), sentences=True)
        elif fname == "concepts":
            limit = string2int(fparm, max=50, fname=fname)
            parms["concepts"] = ConceptsOptions(limit=limit)
        elif fname == "emotion":
            parms["emotion"] = EmotionOptions()
        elif fname == "entities":
            limit = string2int(fparm, max=250, fname=fname)
            parms["entities"] = EntitiesOptions(limit=limit, mentions=True, sentiment=True, emotion=True)
        elif fname == "keywords":
            limit = string2int(fparm, max=250, fname=fname)
            parms["keywords"] = KeywordsOptions(limit=3, sentiment=True, emotion=True)
        elif fname == "relations":
            parms["relations"] = RelationsOptions()
        elif fname == "semantic_roles":
            limit = string2int(fparm, max=250, fname=fname)
            parms["semantic_roles"] = SemanticRolesOptions(limit=limit, keywords=True, entities=True)
        elif fname == "sentiment":
            parms["sentiment"] = SentimentOptions()
        elif fname == "categories":
            limit = string2int(fparm, max=10, fname=fname)
            parms["categories"] = CategoriesOptions(explanation=False, limit=limit)
    return parms


def get_nested(thedict, thekey, sep="_"):
    """Helper function to get a dot-separated nested key from a dictionary or return None if the key does not exist"""
    # Note: this throws an exception if something that is expected to be a nested dict is not.
    keylist = thekey.split(sep)
    cur = thedict
    for curkey in keylist:
        cur = cur.get(curkey)
        if cur is None:
            return None
    return cur


class IbmNluAnnotator(Annotator):

    def __init__(
        self,
        url: str = None,
        apikey: str = None,
        ibm_features: Optional[Features] = None,
        which_features: Optional[Union[str, List[str]]] = None,
        lang: Optional[str] = None,
        outset_name: str = "",
        doc_feature_map: Optional[dict] = None,
        entity_type_map: Optional[dict] = None,
        debug: bool = False,
    ):
        """
        Create an IbmNluAnnotator.

        Args:
            url:  the IBM service URL to use.
            apikey: the IBM service API key to use.
            ibm_features: a pre-initialized ibm Features object that defines which kinds of analyses should get
                carried out.
            which_features: a comma separated list or a python list of features to return,
                possible values are: concepts, emotion, entities,
                keywords, sentiment, categories, syntax.
                (NOTE: not yet implemented: relations, semantic_roles)
                For some of these features,
                it is possible to add additional settings by appending them separated by a colon: concepts:10 (return
                a maximum of 10 concepts); keywords:10 (return a maximum of 10 keywords); categories:3 (return
                a maximum or 3 categories, max value is 10). This is ignored if ibm_features are set.
                If neither this nor ibm_features is specified, the default is "syntax". The actual ibm_features
                used are available in the attribute `ibm_features` of the object after initialization.
            lang: if not None, the ISO 639-1 code of the language the text is in. If None, automatically
                determines the language and stores it as a document feature according to the doc_feature_map parameter.
            outset_name: the name of the annotation set where to create the annotations (default: "")
            doc_feature_map: a map that maps original IBM features to document features. If a IBM features is mapped
                to None, that feature is not stored. Supported mapping keys are: language
            entity_type_map: a map that maps original entity types to annotation types. Only the types in the map
                are affected, others are used unchanged.
        """
        # See https://cloud.ibm.com/apidocs/natural-language-understanding?code=python
        if not url or not apikey:
            raise Exception("Parameters url and apikey are required.")
        authenticator = IAMAuthenticator(apikey)
        nlu = NaturalLanguageUnderstandingV1(version="2021-08-01", authenticator=authenticator)
        nlu.set_service_url(url)
        self.nlu = nlu
        self.lang = lang
        if doc_feature_map is None:
            doc_feature_map = {x: x for x in ["language", "concepts", "emotion", "keywords", "sentiment", "categories"]}
        if entity_type_map is None:
            self.entity_type_map = {}
        else:
            self.entity_type_map = entity_type_map
        self.doc_feature_map = doc_feature_map
        self.outset_name = outset_name

        self.debug = debug
        self.logger = init_logger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
        if ibm_features:
            self.ibm_features = ibm_features
        else:
            if which_features is None:
                which_features = "syntax"
            fparms = which2ibm_features(which_features)
            self.ibm_features = Features(**fparms)

    def __call__(self, doc, **kwargs):
        resp = self.nlu.analyze(
            text=doc.text,
            features=self.ibm_features,
            language=self.lang
        ).get_result()
        outset = doc.annset(self.outset_name)
        if self.debug:
            tmp = json.dumps(resp, indent=2)
            self.logger.debug(f"Result:\n{tmp}")
        if "language" in resp:
            fname = self.doc_feature_map["language"]
            if fname:
                doc.features[fname] = resp["language"]
        if "entities" in resp:
            ents = resp["entities"]
            for ent in ents:
                etype = ent["type"]
                if self.entity_type_map.get(etype) is not None:
                    etype = self.entity_type_map[etype]
                fmap = {}
                for fname in ["relevance", "confidence", "sentiment.score", "sentiment.label",
                              "disambiguation.subtype", "disambiguation.name", "disambiguation.dbpedia_resource"]:
                    val = get_nested(ent, fname, sep=".")
                    if val is not None:
                        fmap[fname] = val
                mentions = ent["mentions"]
                for mention in mentions:
                    start, end = mention["location"]
                    fmap["mention_confidence"] = mention["confidence"]
                    outset.add(start, end, etype, fmap)
        if "concepts" in resp:
            fname = self.doc_feature_map["concepts"]
            if fname:
                doc.features[fname] = resp["concepts"]
        if "categories" in resp:
            fname = self.doc_feature_map["categories"]
            if fname:
                doc.features[fname] = resp["categories"]
        if "emotion" in resp:
            fname = self.doc_feature_map["emotion"]
            emotion_dict = resp["emotion"]["document"]["emotion"]
            fmap = {}
            for kname, value in emotion_dict.items():
                doc.features[fname+"_"+kname] = value
        if "keywords" in resp:
            fname = self.doc_feature_map["keywords"]
            if fname:
                doc.features[fname] = resp["keywords"]
        if "sentiment" in resp:
            fname = self.doc_feature_map["sentiment"]
            sentiment_dict = resp["sentiment"]["document"]
            fmap = {}
            for kname, value in sentiment_dict.items():
                doc.features[fname+"_"+kname] = value
        if "syntax" in resp:
            tokens = resp["syntax"]["tokens"]
            for token in tokens:
                start, end = token["location"]
                fmap = {}
                for fname in ["part_of_speech", "lemma"]:
                    if fname in token:
                        fmap[fname] = token[fname]
                outset.add(start, end, "Token", fmap)
            if "sentences" in resp["syntax"]:
                sentences = resp["syntax"]["sentences"]
            else:
                sentences = []
            for sentence in sentences:
                start, end = sentence["location"]
                outset.add(start, end, "Sentence")
        return doc





