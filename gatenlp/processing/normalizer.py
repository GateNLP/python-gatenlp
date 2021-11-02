"""
Module that provides classes for normalizers. Normalizers are annotators which change the text of selected
 annotations or the entire text of the document.
Since the text of a document is immutable, such Normalizers return a new document with the modified text.
Since the text is modified any annotations present in the document may be invalid, therefore all annotations
are removed when the new document is returned. Document features are preserved. Any changelog is preserved but
the normalization is not logged.
"""
from unicodedata import normalize
from gatenlp import Document
from gatenlp.processing.annotator import Annotator


class Normalizer(Annotator):
    """
    Base class of all normalizers.
    """
    pass


class TextNormalizer(Normalizer):
    """
    Annotator which creates a new, unicode-normalized document from an existing document.
    """
    def __init__(self, form="NFKC"):
        """
        Create a TextNormalizer.

        Args:
            form: the unicode normal form to use. Possible values are "NFC", "NCKC", "NFD" and "NFKD"
        """
        self.form = form

    def __call__(self, doc, **kwargs):
        newtext = normalize(self.form, doc.text)
        newdoc = Document(newtext)
        newdoc.features.update(doc.features)
        return newdoc
