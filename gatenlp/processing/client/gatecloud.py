"""
GATE Cloud annotator client.
"""
import logging
import time
import requests
from requests.auth import HTTPBasicAuth

from gatenlp.processing.annotator import Annotator
from gatenlp.utils import init_logger


class GateCloudAnnotator(Annotator):
    """
    This annotator sends the text of a document to a GATE Cloud (https://cloud.gate.ac.uk/) endpoint and uses the
    returned result to create annotations.
    """

    def __init__(
        self,
        api_key=None,
        api_password=None,
        url=None,
        ann_types=None,
        map_types=None,
        outset_name="",
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
            outset_name: the annotation set in which to store the annotations
            min_delay_ms: minimum time in milliseconds between two subsequent requests to the server
        """
        self.api_key = api_key
        self.api_password = api_password
        self.url = url
        self.map_types = map_types
        self.min_delay_s = min_delay_ms / 1000.0
        self.outset_name = outset_name
        if ann_types:
            if isinstance(ann_types, str):
                self.ann_types = ann_types
            elif isinstance(ann_types, list):
                self.ann_types = ",".join(
                    [at if at.startswith(":") else ":" + at for at in ann_types]
                )
            else:
                raise Exception(
                    "ann_types mist be a string of types like ':Person,:Location' or a list of types"
                )
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
        hdrs = {
            "Content-Type": "text/plain; charset=UTF-8",
            "Accept": "application/gate+json",
        }
        params = {}
        if self.ann_types:
            params["annotations"] = self.ann_types
        # NOTE: not sure when this is needed, for now, disabled
        # next_annid = doc.annset(self.outset_name)._next_annid
        # params["nextAnnotationId"] = str(next_annid)
        # self.logger.debug(f"Sending text={text}, params={params}")
        if self.api_key:
            response = requests.post(
                url,
                data=text.encode("utf-8"),
                headers=hdrs,
                params=params,
                auth=HTTPBasicAuth(self.api_key, self.api_password),
            )
        else:
            response = requests.post(
                url, data=text.encode("utf-8"), headers=hdrs, params=params
            )
        scode = response.status_code
        if scode != 200:
            raise Exception(f"Something went wrong, received status code {scode}")
        json = response.json()
        ents = json.get("entities", {})
        annset = doc.annset(self.outset_name)
        for typename, anns in ents.items():
            for anndata in anns:
                feats = {}
                start, end = (
                    None,
                    None,
                )  # cause an exception if the return data does not have indices
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

