"""
TextRazor client.
"""
import logging
import time
import requests

from gatenlp.processing.annotator import Annotator
from gatenlp.utils import init_logger


class TextRazorTextAnnotator(Annotator):
    """
    An annotator that sends document text to the TextRazor Annotation service (https://www.textrazor.com/)
    and uses the result to annotate the document.

    NOTE: this annotator and how it can get parametrized will still change!
    """

    def __init__(
        self,
        url=None,  # use default
        auth_token=None,
        lang=None,  # if None/not specified, TextRazor auto-detects
        extractors=None,
        outset_name="",
        min_delay_ms=501,
    ):
        """
        Create a TextRazorTextAnnotator.

        Args:
            lang: if specified, override the auto-detected language of the text
            auth_token: the authentication token needed to use the service
            url: the annotation service endpoint, is None, the default endpoint  https://api.textrazor.com is used
            extractors: a list of extractor names or a string with comma-separated extractor names to add to the
               minimum extractors (words, sentences). If None uses words, sentences, entities.
               NOTE: currently only words, sentences, entities is supported.!
            outset_name: the annotationset to put the new annotations in
            min_delay_ms: minimum time in ms to wait between requests to the server
        """
        if url is None:
            url = "https://api.textrazor.com"
        self.url = url
        self.lang = lang
        self.outset_name = outset_name
        self.auth_token = auth_token
        self.min_delay_s = min_delay_ms / 1000.0
        self.logger = init_logger()
        # self.logger.setLevel(logging.DEBUG)
        self._last_call_time = 0
        if extractors is not None:
            if isinstance(extractors, str):
                extractors = extractors.split(",")
            if isinstance(extractors, list):
                allextrs = set()
                allextrs.update(extractors)
                allextrs.update(["words", "sentences"])
                self.extractors = ",".join(list(allextrs))
            else:
                raise Exception("Odd extractors, must be list of strings or string")
        else:
            self.extractors = "words,sentences,entities"

    def __call__(self, doc, **kwargs):
        delay = time.time() - self._last_call_time
        if delay < self.min_delay_s:
            time.sleep(self.min_delay_s - delay)
        text = doc.text
        hdrs = {
            # 'Content-Type': 'text/plain; charset=UTF-8',
            # 'Accept-encoding': 'gzip'  # TODO: to enable compressed responses
            # 'Content-encoding': 'gzip'  # TODO: to enable compressed requests
            "X-TextRazor-Key": self.auth_token
        }
        data = {"text": text.encode("UTF-8")}
        if self.extractors:
            data["extractors"] = self.extractors
        if self.lang:
            data["languageOverride"] = self.lang
        self.logger.debug(f"Sending request to {self.url}, data={data}, headers={hdrs}")
        response = requests.post(
            self.url,
            # params=params,
            data=data,
            headers=hdrs,
        )
        scode = response.status_code
        if scode != 200:
            raise Exception(f"Something went wrong, received status code {scode}")
        json = response.json()
        ok = json.get("ok", False)
        if not ok:
            raise Exception(f"Something went wrong, did not get OK, json: {json}")
        self.logger.debug(f"Response JSON: {json}")
        resp = json.get("response", {})
        entities = resp.get("entities", [])
        sentences = resp.get("sentences", [])
        categories = resp.get("categories", [])
        topics = resp.get("topics", [])
        entailments = resp.get("entailments", [])
        relations = resp.get("relations", [])
        properties = resp.get("properties", [])
        nounphrases = resp.get("nounPhrases", [])
        language = resp.get("language")
        languageIsReliable = resp.get("languageIsReliable")
        tok2off = {}  # maps token idxs to tuples (start,end)
        annset = doc.annset(self.outset_name)
        for s in sentences:
            sentstart = None
            sentend = None
            words = s.get("words", [])
            end = None
            for word in words:
                start = word["startingPos"]
                end = word["endingPos"]
                if sentstart is None:
                    sentstart = start
                tokidx = word["position"]
                feats = {}
                feats["partOfSpeech"] = word["partOfSpeech"]
                feats["lemma"] = word["lemma"]
                if word.get("stem"):
                    feats["stem"] = word["stem"]
                annset.add(start, end, "Token", features=feats)
                tok2off[tokidx] = (start, end)
            if end is not None:
                sentend = end
            if sentstart is not None and sentend is not None:
                annset.add(sentstart, sentend, "Sentence")
        for ent in entities:
            feats = {}
            for fname in [
                "wikiLink",
                "entityEnglishId",
                "wikidataId",
                "relevanceScore",
                "confidenceScore",
                "type",
                "freebaseId",
                "entityId",
                "freebaseTypes",
            ]:
                if fname in ent:
                    feats[fname] = ent[fname]
            annset.add(ent["startingPos"], ent["endingPos"], "Entity", feats)
        return doc

