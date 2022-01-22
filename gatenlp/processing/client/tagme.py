"""
TagMe client.
"""
import time
import requests

from gatenlp.processing.annotator import Annotator
from gatenlp.utils import init_logger
from gatenlp.offsetmapper import OffsetMapper


class TagMeAnnotator(Annotator):
    """
    An annotator that sends text to the TagMe Annotation service
    (https://sobigdata.d4science.org/group/tagme/tagme)
    and uses the result to annotate the document.
    """

    def __init__(
        self,
        url=None,
        auth_token=None,
        lang="en",
        ann_type="Mention",
        task="tag",  # or spot
        outset_name="",
        min_delay_ms=501,
        tweet=False,
        include_all_spots=False,
        long_text=None,
        epsilon=None,
        link_pattern="https://{0}.wikipedia.org/wiki/{1}",
    ):
        """
        Create a TagMeAnnotator.

        Args:
            url: the annotation service endpoint, is None, the default endpoint for the task (spot or tag) is used
            auth_token: the authentication token needed to use the service
            lang: the language of the text, one of 'de', 'en' (default), 'it'
            ann_type: the annotation type for the new annotations, default is "Mention"
            task: one of "spot" (only find mentions) or "tag" (find mentions and link), default is "tag"
            outset_name: the annotationset to put the new annotations in
            min_delay_ms: minimum time in ms to wait between requests to the server
            tweet: if True, TagMe expects a Tweet (default is False)
            include_all_spots: if True, include spots that cannot be linked (default is False)
            long_text: if not None, the context length to use (default: None)
            epsilon: if not None, the epsilong value (float) to use (default: None)
            link_pattern: the URL pattern to use to turn the "title" returned from TagMe into an actual link. The
               default is "https://{0}.wikipedia.org/wiki/{1}" where {0} gets replaced with the language code and
               {1} gets replaced with the title.
        """
        if url is None:
            if task == "tag":
                url = "https://tagme.d4science.org/tagme/tag"
            elif task == "spot":
                url = "https://tagme.d4science.org/tagme/spot"
            else:
                raise Exception("task must be 'tag' or 'spot'")
        assert lang in ["en", "de", "it"]
        if long_text is not None:
            assert isinstance(long_text, int)
        if epsilon is not None:
            assert isinstance(epsilon, float)
        self.long_text = long_text
        self.epsilon = epsilon
        self.lang = lang
        self.auth_token = auth_token
        self.url = url
        self.tweet = tweet
        self.include_all_spots = include_all_spots
        self.outset_name = outset_name
        self.min_delay_s = min_delay_ms / 1000.0
        self.logger = init_logger()
        # self.logger.setLevel(logging.DEBUG)
        self._last_call_time = 0
        self.ann_type = ann_type
        self.link_pattern = link_pattern

    def __call__(self, doc, **kwargs):
        if "tweet" in kwargs:
            tweet = kwargs["tweet"]
        else:
            tweet = self.tweet
        delay = time.time() - self._last_call_time
        if delay < self.min_delay_s:
            time.sleep(self.min_delay_s - delay)
        text = doc.text
        hdrs = {
            "Content-Type": "text/plain; charset=UTF-8",
            "Accept": "application/gate+json",
        }
        params = {
            "text": text,
            "gcube-token": self.auth_token,
            "lang": self.lang,
        }
        if self.include_all_spots:
            params["include_all_spots"] = "true"
        if tweet:
            params["tweet"] = "true"
        if self.long_text is not None:
            params["long_text"] = self.long_text
        if self.epsilon is not None:
            params["epsilon"] = self.epsilon
        response = requests.post(self.url, params=params, headers=hdrs)
        scode = response.status_code
        if scode != 200:
            raise Exception(f"Something went wrong, received status code {scode}")
        json = response.json()
        # self.logger.debug(f"Response JSON: {json}")
        ents = json.get("annotations", {})
        annset = doc.annset(self.outset_name)
        om = OffsetMapper(text)
        for ent in ents:
            start = ent["start"]
            end = ent["end"]
            start, end = om.convert_to_python([start, end])
            feats = {}
            title = ent.get("title")
            if title is not None:
                if self.link_pattern:
                    feats["url"] = self.link_pattern.format(self.lang, title)
                else:
                    feats["title"] = title
            for fname in ["id", "rho", "link_probability", "lp"]:
                fval = ent.get(fname)
                if fval is not None:
                    feats[fname] = fval
            # self.logger.debug(f"Adding annotation {start},{end},{feats}")
            annset.add(start, end, self.ann_type, features=feats)
        return doc

