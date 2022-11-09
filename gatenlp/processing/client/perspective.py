"""
Perspective client.
"""
import time

from typing import Optional, Union, List, Dict
from gatenlp.processing.annotator import Annotator
from gatenlp.utils import init_logger


class PerspectiveAnnotator(Annotator):
    """
    An annotator that sends text to the Perspective classification service
    (see https://perspectiveapi.com/)
    and uses the result to set either document or annotation features.
    """

    def __init__(
        self,
        url: Optional[str] = "https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
        auth_token: str = "",
        requested_attributes: Optional[List[str]] = None,
        requested_attributes_feature: Optional[str] = None,
        do_not_store: bool = True,
        langs: Optional[Union[str, List[str]]] = None,
        langs_feature: Optional[str] = None,
        annset_name: Optional[str] = "",
        ann_type: Optional[str] = None,
        ann_feature: Optional[str] = None,
        attr2feature: Optional[Dict[str, str]] = None,
        min_delay_ms: int = 1000,
    ):
        """
        Create a Perspective annotator.

        Args:
            url: the annotation service endpoint, if None, the default endpoint URL
            auth_token: (required) the authentication token needed to use the service
            requested_attributes: (required) a list of attributes to return. Note that not all attributes are
                available for all languages!
            requested_attributes_feature: if specified, get the requested attributes list from that doc/ann feature
                if it exists (fall back to requested_attributes)
            do_not_store: if True, do not allow the text to get stored (default: True)
            langs: None indiciates auto-detect, otherwise the language code or a list of language codes.
            langs_feature: if the text is taken from an annotation, the feature of that annotation that contains
                the language code or list of language codes. If the feature does not exist or is empty, falls back
                to langs. If the text is taken from the document, a document feature that contains the language code
                or list of language codes. 
            annset_name: if an annotation type is specified, the name of the annotation set to use
            ann_type: if this is specified, the text of those annoations is getting classified and
                the result is stored as annotaiton features. Otherwise, the whole document is classified
                and the result is stored as document features.
            ann_feature: if ann_type is specified, and this is also specified, the text is taken from
                that feature instead of the underlying document text.
            attr2feature: a dictionary mapping attribute names to feature names. Note that each attribute name is
                made of the actual attribute (e.g. "TOXICITY") with the score type appended after an underscore,
                e.g. "_PROBABILITY", giving "TOXICITY_PROBABILITY". Only the summary scores are used.
            min_delay_ms: minimum time in ms to wait between requests to the server (1000)
        """
        try:
            from googleapiclient import discovery
        except Exception as ex:
            raise Exception(f"Package google-api-python-client not installed?", ex)
        assert auth_token
        assert requested_attributes
        self.auth_token = auth_token
        self.url = url
        self.min_delay_s = min_delay_ms / 1000.0
        self.logger = init_logger()
        # self.logger.setLevel(logging.DEBUG)
        self._last_call_time = 0
        self.ann_type = ann_type
        self.ann_feature = ann_feature
        self.langs = langs
        self.langs_feature = langs_feature
        self.attr2feature = attr2feature
        self.annset_name = annset_name
        self.do_not_store = do_not_store
        self.requested_attributes = requested_attributes
        self.requested_attributes_feature = requested_attributes_feature
        self.client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=self.auth_token,
            discoveryServiceUrl=self.url,
            static_discovery=False,
        )

    def _call_api(self, text, langs=None, requested_attributes=None, attr2feature=None):
        """Send text to API respecting min delay and get back dict"""
        delay = time.time() - self._last_call_time
        if delay < self.min_delay_s:
            time.sleep(self.min_delay_s - delay)
        request = {
            "comment": {"text": text},
            "requestedAttributes": {n: {} for n in requested_attributes},
            "doNotStore": self.do_not_store,
        }
        if langs is not None:
            if isinstance(langs, str):
                langs = [langs]
            request["languages"] = langs
        # pylint complains about this claiming that self.client does not have an attribute
        # comments but this is not true.
        # disabling that error message
        response = self.client.comments().analyze(body=request).execute()  # pylint: disable=E1101
        ret = {}
        scoredata = response["attributeScores"]
        for name, data in scoredata.items():
            val = data["summaryScore"]["value"]
            typ = data["summaryScore"]["type"]
            if attr2feature is not None:
                name = attr2feature.get(name, name)
            ret[name+"_"+typ] = val
        name = "languages"
        if attr2feature is not None:
            name = attr2feature(name, name)
        ret[name] = response["languages"]
        return ret

    def __call__(self, doc, **kwargs):
        if self.ann_type is not None:
            annset = doc.annset(self.annset_name).with_type(self.ann_type)
            for ann in annset:
                if self.ann_feature:
                    txt = ann.features.get(self.ann_feature, "")
                else:
                    txt = doc[ann]
                langs = self.langs
                if self.langs_feature:
                    langs = ann.features.get(self.langs_feature, langs)
                requested_attributes = self.requested_attributes
                if self.requested_attributes_feature:
                    requested_attributes = ann.features.get(self.requested_attributes_feature, requested_attributes)
                ret = self._call_api(txt, langs=langs,
                                     attr2feature=self.attr2feature, requested_attributes=requested_attributes)
                if isinstance(ret, dict):
                    ann.features.update(ret)
        else:
            langs = self.langs
            if self.langs_feature:
                langs = doc.features.get(self.langs_feature, langs)
            requested_attributes = self.requested_attributes
            if self.requested_attributes_feature:
                requested_attributes = doc.features.get(self.requested_attributes_feature, requested_attributes)
            ret = self._call_api(doc.text, langs=langs,
                                 attr2feature=self.attr2feature, requested_attributes=requested_attributes)
            if isinstance(ret, dict):
                doc.features.update(ret)
        return doc
