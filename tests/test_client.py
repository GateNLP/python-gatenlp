import os
from gatenlp import logger, Document


class TestClient01:
    # not much we can except importing the class
    def test_client01a(self):
        """
        Unit test method (make linter happy)
        """
        from gatenlp.processing.client import TagMeAnnotator
        from gatenlp.processing.client import ElgTextAnnotator
        from gatenlp.processing.client import GateCloudAnnotator
        from gatenlp.processing.client import TextRazorTextAnnotator
