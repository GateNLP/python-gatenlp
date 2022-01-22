"""
ELG client.
"""
import json
import time
import requests
import logging
from elg import Authentication
from elg.utils import get_domain, get_metadatarecord

from gatenlp.processing.annotator import Annotator
from gatenlp.utils import init_logger
from gatenlp import Span

class ElgTextAnnotator(Annotator):
    # NOTE: maybe we should eventually always use the elg package and the elg Service class!
    #   however, currently their way how handling auth is done is too limiting see issues #8, #9

    # NOTE: use template and return the URL from a method or use elg.utils
    ELG_SC_LIVE_URL_PREFIX = "https://live.european-language-grid.eu/auth/realms/ELG/protocol/openid-connect/auth?"
    ELG_SC_LIVE_URL_PREFIX += (
        "client_id=python-sdk&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code"
    )
    ELG_SC_LIVE_URL_OFFLINE = ELG_SC_LIVE_URL_PREFIX + "&scope=offline_access"
    ELG_SC_LIVE_URL_OPENID = ELG_SC_LIVE_URL_PREFIX + "&scope=openid"

    ELG_SC_DEV_URL_PREFIX = "https://dev.european-language-grid.eu/auth/realms/ELG/protocol/openid-connect/auth?"
    ELG_SC_DEV_URL_PREFIX += (
        "client_id=python-sdk&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code"
    )
    ELG_SC_DEV_URL_OFFLINE = ELG_SC_DEV_URL_PREFIX + "&scope=offline_access"
    ELG_SC_DEV_URL_OPENID = ELG_SC_DEV_URL_PREFIX + "&scope=openid"
    """
    An annotator that sends text to one of the services registered with the European Language Grid
    (https://live.european-language-grid.eu/) and uses the result to create annotations.
    """

    def __init__(
        self,
        url=None,
        sync_mode=True,
        servicenr=None,
        auth=None,
        auth_file=None,
        timeout=None,
        success_code=None,
        access_token=None,
        refresh_access=False,
        outset_name="",
        min_delay_ms=501,
        anntypes_map=None,
        debug=False,
    ):
        """
        Create an ElgTextAnnotator.

        NOTE: initialization can fail with an exception if success_code is specified and retrieving the
        authentification information fails.

        Args:
            url:  the annotation service URL to use. If not specified, the service parameter must be specified.
            sync_mode: if True call the service synchronously, otherwise asynchronously. Note that the
                url must match the sync_mode. E.g.
                https://live.european-language-grid.eu/execution/async/process/SERVICE vs
                https://live.european-language-grid.eu/execution/process/SERVICE
            servicenr: the ELG service number or a tuple (servicenumber, domain). This requires the elg package.
                This may raise an exception. If successful, the url and service_meta attributes are set.
            auth: a pre-initialized ELG Authentication object. Requires the elg package. If not specified, the
                success_code or access_token parameter must be specified for authentication, or none of those
                to use an ELG-like endpoint without required authentication.
            auth_file: the path to an auth_file created in advance
            timeout: timeout in seconds or None to leave unspecified
            success_code: the success code returned from the ELG web page for one of the URLs to obtain
                success codes. This will try to obtain the authentication information and store it in the
                `auth` attribute.  Requires the elg package.
                To obtain a success code, go the the ELG_SC_LIVE_URL_OPENID or ELG_SC_LIVE_URL_OFFLINE url
                and log in with your ELG user id, this will show the success code that can be copy-pasted.
            access_token: the access token token for the ELG service. Only used if auth or success_code are not
                specified. The access token is probably only valid for a limited amount of time. No refresh
                will be done and once the access token is invalid, calling `__call__` will fail with an exception.
                The access token can be obtained using the elg package or copied from the "Code samples" tab
                on the web page for a service after logging in.
            refresh_access: if True, will try to refresh the access token if auth or success_code was specified and
                refreshing is possible. Ignored if only access_token was specified
            outset_name: the name of the annotation set where to create the annotations (default: "")
            min_delay_ms: the minimum delay time between requests in milliseconds (default: 501 ms)
            anntypes_map: a map for renaming the annotation type names from the service to the ones to use in
               the annotated document.
        """
        if [x is not None for x in [url, servicenr]].count(True) != 1:
            raise Exception("Exactly one of service or url must be specified")
        if [x is not None for x in [auth, success_code, access_token]].count(True) > 1:
            raise Exception(
                "None or exactly one of auth, success_code, or access_token must be specified"
            )
        self.access_token = access_token
        self.success_code = success_code
        self.auth = auth
        self.url = url
        self.servicenr = servicenr
        self.service_meta = None
        self.refresh_access = refresh_access
        self.sync_mode = sync_mode
        self.timeout = timeout
        self.debug = debug
        # first check if we need to import the elg package
        if access_token:
            self.refresh_access = False
        if servicenr is not None:
            if isinstance(servicenr, tuple):
                service_id, domain = servicenr
            else:
                service_id = servicenr
                domain = get_domain("live")
            self.service_meta = get_metadatarecord(service_id, domain, False, None, False)
            if sync_mode:
                self.url = self.service_meta["service_info"]["elg_execution_location_sync"]
            else:
                self.url = self.service_meta["service_info"]["elg_execution_location"]
        if success_code is not None:
            self.auth = Authentication.from_success_code(success_code, domain="live")
        if auth_file is not None:
            self.auth = Authentication.from_json(auth_file)
        if self.auth:
            self.access_token = self.auth.access_token
        self.min_delay_s = min_delay_ms / 1000.0
        self.anntypes_map = anntypes_map
        self.outset_name = outset_name
        self.logger = init_logger(__name__)
        self.response_json = None
        if debug:
            self.logger.setLevel(logging.DEBUG)
        self._last_call_time = 0

    def __call__(self, doc, **kwargs):
        # if necessary and possible, refresh the access token
        if self.refresh_access and self.auth:
            self.auth.refresh_if_needed()
        delay = time.time() - self._last_call_time
        if delay < self.min_delay_s:
            time.sleep(self.min_delay_s - delay)
        request_json = json.dumps(
            {"type": "text", "content": doc.text, "mimeType": "text/plain"}
        )
        hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.access_token:
            hdrs["Authorization"] = f"Bearer {self.access_token}"
        if self.sync_mode:
            response = self._call_sync(request_json, hdrs)
        else:
            response = self._call_async(request_json, hdrs)

        assert response.encoding.lower() == "utf-8"
        assert response.status_code == 200
        response_json = response.json()
        if self.debug:
            self.logger.debug(f"Response JSON: {response_json}")
        self.response_data = response_json
        ents = response_json.get("response", {}).get("annotations", {})
        annset = doc.annset(self.outset_name)
        for ret_anntype, ret_anns in ents.items():
            if self.anntypes_map:
                anntype = self.anntypes_map.get(ret_anntype, ret_anntype)
            else:
                anntype = ret_anntype
            for ret_ann in ret_anns:
                start = ret_ann["start"]
                end = ret_ann["end"]
                feats = ret_ann.get("features", {})
                # start, end = om.convert_to_python([start, end])
                annset.add(start, end, anntype, features=feats)
        return doc

    def _call_sync(self, request_json, hdrs):
        response = requests.post(self.url, data=request_json, headers=hdrs, timeout=self.timeout)
        if response.status_code != 200:
            raise Exception(
                f"Something went wrong, received status code/text {response.status_code} / {response.text}"
            )
        return response

    def _call_async(self, request_json, hdrs):
        # see https://gitlab.com/european-language-grid/platform/python-client/-/blob/master/elg/service.py
        response = requests.post(
            self.url,
            data=request_json,
            headers=hdrs, timeout=self.timeout)
        if response.status_code >= 400:
            raise Exception(
                f"Something went wrong, received status code/text {response.status_code} / {response.text}"
            )
        response = response.json()["response"]
        assert response["type"] == "stored"
        hdrs.pop("Content-Type")
        uri = response["uri"]
        response = requests.get(uri, headers=hdrs)
        jresp = response.json()
        waiting_time = time.time()
        while response.ok and "progress" in response.json().keys():
            percent = jresp["progress"]["percent"]
            time.sleep(1)
            response = requests.get(uri, headers=hdrs, timeout=self.timeout)
            jresp = response.json()
            if time.time() - waiting_time > (self.timeout if self.timeout is not None else float("inf")):
                raise Exception("No async result returned within timeout")
        return response


def udptoken2tokens(udptoken_set, udpsentence_set, outset, token_type="Token", mwt_type="MWT"):
    for sent in udpsentence_set:
        udptokens4sent = udptoken_set.within(sent)
        anns4sent = []
        for utoken in udptokens4sent:
            words = utoken.features["words"]
            if len(words) == 1:
                ann = outset.add(utoken.start, utoken.end, token_type, features=words[0])
                anns4sent.append(ann)
            else:
                spans = Span.squeeze(utoken.start, utoken.end, len(words))
                assert len(words) == len(spans)
                annids = []
                for word, span in zip(words, spans):
                    ann = outset.add(span.start, span.end, token_type, features=word)
                    annids.append(ann.id)
                    anns4sent.append(ann)
                outset.add(utoken.start, utoken.end, mwt_type, features=dict(word_ids=annids))
        # now patch up the head ids: replace id 0 with the annotation id of the containing sentence,
        # and replace all other ids with the annotation id of the corresponding token
        # also replace the "feats" feature with individual features for its contents
        for ann in anns4sent:
            if ann.features["head"] == 0:
                ann.features["head"] = sent.id
            else:
                ann.features["head"] = anns4sent[ann.features["head"]-1].id
            feats = ann.features.get("feats")
            if feats is not None:
                assignments = feats.split("|")
                for assignment in assignments:
                    name, value = assignment.split("=")
                    ann.features[name] = value
                ann.features.pop("feats")


