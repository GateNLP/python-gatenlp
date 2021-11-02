"""
Module for testing the TextNormalizer
"""
from gatenlp.document import Document
from gatenlp.processing.normalizer import TextNormalizer

TEXT_NFC = "Äffin ａｂｃＡＢＣ"

TEXT_NFKC = "Äffin abcABC"
TEXT_NFD = "Äffin ａｂｃＡＢＣ"
TEXT_NFKD = "Äffin abcABC"


class TestTextNormalizer1:

    def test_create(self):
        """
        Unit test method (make linter happy)
        """
        doc1 = Document(TEXT_NFC, features=dict(a=1))

        tn_nfkc = TextNormalizer(form="NFKC")
        doc2 = tn_nfkc(doc1)
        assert doc2.text == TEXT_NFKC
        assert doc2.features == dict(a=1)

        tn_nfd = TextNormalizer(form="NFD")
        doc3 = tn_nfd(doc1)
        assert doc3.text == TEXT_NFD

        tn_nfkd = TextNormalizer(form="NFKD")
        doc4 = tn_nfkd(doc1)
        assert doc4.text == TEXT_NFKD

        tn_nfc = TextNormalizer(form="NFC")
        doc5 = tn_nfc(doc3)
        assert doc5.text == TEXT_NFC
