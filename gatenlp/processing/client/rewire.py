"""
Rewire client.
"""
import time
import requests

from typing import Optional
from gatenlp.processing.annotator import Annotator
from gatenlp.utils import init_logger


class RewireAnnotator(Annotator):
    """
    An annotator that sends text to the Rewire classification service
    (see https://rewire.online/rewire-api-access/)
    and uses the result to set either document or annotation features.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        auth_token: Optional[str] = None,
        # lang="en",
        annset_name: Optional[str] = "",
        ann_type: Optional[str] = None,
        ann_feature: Optional[str] = None,
        feature_hate: str = "hate",
        feature_abuse: str = "abuse",
        min_delay_ms=0,
    ):
        """
        Create a Rewire annotator.

        Args:
            url: the annotation service endpoint, if None, the default endpoint URL
            auth_token: the authentication token needed to use the service, this is required!
            annset_name: if an annotation type is specified, the name of the annotation set to use
            ann_type: if this is specified, the text of those annoations is getting classified and
                the result is stored as annotaiton features. Otherwise, the whole document is classified
                and the result is stored as document features.
            ann_feature: if ann_type is specified, and this is also specified, the text is taken from
                that feature instead of the underlying document text.
            feature_hate: if annotations get classified, the name of the feature to set with the
                hate score ("hate")
            feature_abuse: if annotations get classified, the name of the feature to set with the
                abuse score ("abuse"
            min_delay_ms: minimum time in ms to wait between requests to the server
        """
        if url is None:
            url = "https://api.rewire.online/classify"
        self.auth_token = auth_token
        self.url = url
        self.min_delay_s = min_delay_ms / 1000.0
        self.logger = init_logger()
        # self.logger.setLevel(logging.DEBUG)
        self._last_call_time = 0
        self.ann_type = ann_type
        self.ann_feature = ann_feature
        self.feature_hate = feature_hate
        self.feature_abuse = feature_abuse
        self.annset_name = annset_name

    def _call_api(self, text):
        """Send text to API respecting min delay and get back dict"""
        delay = time.time() - self._last_call_time
        if delay < self.min_delay_s:
            time.sleep(self.min_delay_s - delay)
        response = requests.post(
            self.url,
            json=dict(text=text),
            headers={"x-api-key": self.auth_token})
        return response.json()

    def __call__(self, doc, **kwargs):
        if self.ann_type is not None:
            annset = doc.annset(self.annset_name).with_type(self.ann_type)
            for ann in annset:
                if self.ann_feature:
                    txt = ann.features.get(self.ann_feature, "")
                else:
                    txt = doc[ann]
                ret = self._call_api(txt)
                if isinstance(ret, dict):
                    scores = ret["scores"]
                    ann.features[self.feature_hate] = scores["hate"]
                    ann.features[self.feature_abuse] = scores["abuse"]
        else:
            ret = self._call_api(doc.text)
            if isinstance(ret, dict):
                scores = ret["scores"]
                doc.features[self.feature_hate] = scores["hate"]
                doc.features[self.feature_abuse] = scores["abuse"]
        return doc
