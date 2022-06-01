import os
from gatenlp import logger, Document


class TestClient01:
    # not much we can except importing the class
    def test_client01a(self):
        """
        Unit test method (make linter happy)
        """
        from gatenlp.processing.client.tagme import TagMeAnnotator
        from gatenlp.processing.client.elg import ElgTextAnnotator
        from gatenlp.processing.client.gatecloud import GateCloudAnnotator
        from gatenlp.processing.client.textrazor import TextRazorTextAnnotator
