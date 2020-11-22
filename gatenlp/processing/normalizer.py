"""
Module that provides classes for normalizers. Normalizers are annotators which change the text of selected
 annotations or the entire text of the document.
Since the text of a document is immutable, such Normalizers return a new document with the modified text.
Since the text is modified any annotations present in the document may be invalid, therefore all annotations
are removed when the new document is returned. Document features are preserved. Any changelog is preserved but
the normalization is not logged.
"""

from gatenlp.processing.annotator import Annotator


class Normalizer(Annotator):
    """
    Base class of all normalizers.
    """

    pass


class TextNormalizer(Normalizer):
    """
    NOT YET IMPLEMENTED
    """

    pass
