"""
Rewire client.
"""
import time
import requests

from typing import Optional, Dict
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
        attr2feature: Optional[Dict[str,str]] = None,
        min_delay_ms=0,
    ):
        """
        Create a Rewire annotator. The annotator stores the scores returned from the
        Rewire service as features, either in the annotation that gets processed or the document
        features if the whole document is getting processed.

        Args:
            url: the annotation service endpoint, if None, the default endpoint URL
            auth_token: the authentication token needed to use the service, this is required!
            annset_name: if an annotation type is specified, the name of the annotation set to use
            ann_type: if this is specified, the text of those annoations is getting classified and
                the result is stored as annotaiton features. Otherwise, the whole document is classified
                and the result is stored as document features.
            ann_feature: if ann_type is specified, and this is also specified, the text is taken from
                that feature instead of the underlying document text.
            attr2feature: a dictionary mapping the attributes (score names) returned from the
                service to feature names. Currently attributes "hate" and "abuse" are returned.
            min_delay_ms: minimum time in ms to wait between requests to the server
        """
        if url is None:
            url = "https://api.rewire.online/classify"
        assert auth_token
        self.auth_token = auth_token
        self.url = url
        self.min_delay_s = min_delay_ms / 1000.0
        self.logger = init_logger()
        # self.logger.setLevel(logging.DEBUG)
        self._last_call_time = 0
        self.ann_type = ann_type
        self.ann_feature = ann_feature
        self.attr2feature = attr2feature
        self.annset_name = annset_name

    def _call_api(self, text, attr2feature=None):
        """Send text to API respecting min delay and get back dict"""
        delay = time.time() - self._last_call_time
        if delay < self.min_delay_s:
            time.sleep(self.min_delay_s - delay)
        response = requests.post(
            self.url,
            json=dict(text=text),
            headers={"x-api-key": self.auth_token})
        ret = response.json()
        if "message" in ret and "scores" not in ret:
            raise Exception(f"API call problem, message is: {ret['message']}")
        ret = ret["scores"]
        if attr2feature:
            retnew = {}
            for k, v in ret.items():
                knew = attr2feature.get(k, k)
                retnew[knew] = v
            ret = retnew
        return ret

    def __call__(self, doc, **kwargs):
        if self.ann_type is not None:
            annset = doc.annset(self.annset_name).with_type(self.ann_type)
            for ann in annset:
                if self.ann_feature:
                    txt = ann.features.get(self.ann_feature, "")
                else:
                    txt = doc[ann]
                ret = self._call_api(txt, attr2feature=self.attr2feature)
                if isinstance(ret, dict):
                    ann.features.update(ret)
        else:
            ret = self._call_api(doc.text, attr2feature=self.attr2feature)
            if isinstance(ret, dict):
                doc.features.update(ret)
        return doc
