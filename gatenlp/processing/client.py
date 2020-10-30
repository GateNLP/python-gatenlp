"""
Module that provides various Annotators which act as clients to REST annotation services.
"""

import logging
from gatenlp.processing.annotator import Annotator
import requests
from requests.auth import HTTPBasicAuth
from gatenlp.utils import init_logger
import time
from gatenlp.offsetmapper import OffsetMapper

# TODO:
# * support compression send/receive
# * send GATE XML for existing annotations (requires GATE XML serialization writer)
# * send raw HTML or other formats support by the endpoint instead "doc" (which so far is just text)
# * maybe support the 100-continue protocol so far we dont
# * ERROR HANDLING: raise exception vs return None?
class GateCloudAnnotator(Annotator):
    """
    This annotator sends the text of a document to a GATE Cloud (https://cloud.gate.ac.uk/) endpoint and uses the
    returned result to create annotations.
    """

    def __init__(self,
                 api_key=None,
                 api_password=None,
                 url=None,
                 ann_types=None,
                 map_types=None,
                 out_annset="",
                 min_delay_ms=501,
                 ):
        """
        Create a GateCloudAnnotator.

        Args:
            api_key: API key needed to authenticate. Some services can be used in a limited way without
               authentication.
            api_password: API password needed to authenticale.
            url:  the URL of the annotation service endpoint, shown on the GATE Cloud page for the service
            ann_types: this can be used to let the service annotate fewer or more than the default list of annotation
               types. The default list and all possible annotations are shown on the GATE Cloud page for the service.
               Either a string with comma separated annotation types preceded by a colon (e.g. ":Person,:Location")
               or a python list with those type names (e.g. [":Person", ":Location"]). If the list contains type names
               without a leading colon, the colon is added.
            map_types: a dict which maps the annotation types from the service to arbitrary new annotation types,
               any type name not in the map will remain unchanged.
            out_annset: the annotation set in which to store the annotations
            min_delay_ms: minimum time in milliseconds between two subsequent requests to the server
        """
        self.api_key = api_key
        self.api_password = api_password
        self.url = url
        self.map_types = map_types
        self.min_delay_s = min_delay_ms / 1000.0
        self.out_annset = out_annset
        if ann_types:
            if isinstance(ann_types, str):
                self.ann_types = ann_types
            elif isinstance(ann_types, list):
                self.ann_types = ",".join([at if at.startswith(":") else ":"+at for at in ann_types])
            else:
                raise Exception("ann_types mist be a string of types like ':Person,:Location' or a list of types")
        else:
            self.ann_types = None
        self.logger = init_logger()
        self.logger.setLevel(logging.DEBUG)
        self._last_call_time = 0

    def __call__(self, doc, **kwargs):
        delay = time.time() - self._last_call_time
        if delay < self.min_delay_s:
            time.sleep(self.min_delay_s - delay)
        if "url" in kwargs:
            url = kwargs["url"]
        else:
            url = self.url
        text = doc.text
        hdrs = {'Content-Type': 'text/plain; charset=UTF-8', 'Accept': 'application/gate+json'}
        params = {}
        if self.ann_types:
            params["annotations"] = self.ann_types
        # NOTE: not sure when this is needed, for now, disabled
        #next_annid = doc.annset(self.out_annset)._next_annid
        #params["nextAnnotationId"] = str(next_annid)
        # self.logger.debug(f"Sending text={text}, params={params}")
        if self.api_key:
            response = requests.post(url, data=text.encode("utf-8"), headers=hdrs, params=params,
                                     auth=HTTPBasicAuth(self.api_key, self.api_password))
        else:
            response = requests.post(url, data=text.encode("utf-8"), headers=hdrs, params=params)
        scode = response.status_code
        if scode != 200:
            raise Exception(f"Something went wrong, received status code {scode}")
        json = response.json()
        ents = json.get("entities", {})
        annset = doc.annset(self.out_annset)
        for typename, anns in ents.items():
            for anndata in anns:
                feats = {}
                start, end = None, None   # cause an exception if the return data does not have indices
                for fname, fval in anndata.items():
                    if fname == "indices":
                        start, end = fval[0], fval[1]
                    else:
                        feats[fname] = fval
                if self.map_types:
                    typename = self.map_types.get(typename, typename)
                # self.logger.debug(f"Adding annotation {start},{start},{typename},{feats}")
                annset.add(start, end, typename, features=feats)
        return doc


class TagMeAnnotator(Annotator):
    """
    An annotator that sends text to the TagMe Annotation service (https://sobigdata.d4science.org/group/tagme/tagme)
    and uses the result to annotate the document.
    """
    def __init__(self,
                 lang="en",
                 ann_type="Mention",
                 auth_token=None,
                 url=None,
                 task="tag", # or spot
                 out_annset="",
                 min_delay_ms=501,
                 tweet=False,
                 include_all_spots=False,
                 long_text=None,
                 epsilon=None,
                 link_pattern="https://{0}.wikipedia.org/wiki/{1}"
                 ):
        """
        Create a TagMeAnnotator.

        Args:
            lang: the language of the text, one of 'de', 'en' (default), 'it'
            ann_type: the annotation type for the new annotations, default is "Mention"
            auth_token: the authentication token needed to use the service
            url: the annotation service endpoint, is None, the default endpoint for the task (spot or tag) is used
            task: one of "spot" (only find mentions) or "tag" (find mentions and link), default is "tag"
            out_annset: the annotationset to put the new annotations in
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
        assert lang in ['en', 'de', 'it']
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
        self.out_annset = out_annset
        self.min_delay_s = min_delay_ms / 1000.0
        self.logger = init_logger()
        # self.logger.setLevel(logging.DEBUG)
        self._last_call_time = 0
        self.ann_type = ann_type
        self.link_pattern = link_pattern

    def __call__(self, doc, **kwargs):
        if 'tweet' in kwargs:
            tweet = kwargs["tweet"]
        else:
            tweet = self.tweet
        delay = time.time() - self._last_call_time
        if delay < self.min_delay_s:
            time.sleep(self.min_delay_s - delay)
        text = doc.text
        text = doc.text
        hdrs = {'Content-Type': 'text/plain; charset=UTF-8', 'Accept': 'application/gate+json'}
        params = {
            'text': text, 'gcube-token': self.auth_token, 'lang': self.lang,
        }
        if self.include_all_spots:
            params["include_all_spots"] = "true"
        if tweet:
            params["tweet"] = "true"
        if self.long_text is not None:
            params["long_text"] = self.long_text
        if self.epsilon is not None:
            params["epsilon"] = self.epsilon
        response = requests.post(self.url, params=params)
        scode = response.status_code
        if scode != 200:
            raise Exception(f"Something went wrong, received status code {scode}")
        json = response.json()
        # self.logger.debug(f"Response JSON: {json}")
        ents = json.get("annotations", {})
        annset = doc.annset(self.out_annset)
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


class ElgTextAnnotator(Annotator):
    """
    Not yet implemented.
    """
    def __init__(self,
                 auth_token=None,
                 url=None,
                 out_annset="",
                 min_delay_ms=501,
                 ):
        pass

    def __call__(self, doc, **kwargs):
        pass