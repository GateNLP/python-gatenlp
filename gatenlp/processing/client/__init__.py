"""
Module that provides various Annotators which act as clients to REST annotation services.
"""

# We do not perform these convenience import here to allow installing dependencies
# only for the client actually needed. The client needs to get installed from the
# client specific module (e.g. gatenlp.processing.client.elg) directly
# from gatenlp.processing.client.gatecloud import GateCloudAnnotator
# from gatenlp.processing.client.tagme import TagMeAnnotator
# from gatenlp.processing.client.textrazor import TextRazorTextAnnotator
# from gatenlp.processing.client.elg import ElgTextAnnotator
# from gatenlp.processing.client.ibmnlu import IbmNluAnnotator
# from gatenlp.processing.client.googlenlp import GoogleNlpAnnotator


# TODO:
# * support compression send/receive
# * send GATE XML for existing annotations (requires GATE XML serialization writer)
# * send raw HTML or other formats support by the endpoint instead "doc" (which so far is just text)
# * maybe support the 100-continue protocol so far we dont
# * ERROR HANDLING: raise exception vs return None?
