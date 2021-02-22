"""
Module that provides the class GatenlpConfig and the instance gatenlpconfig which stores various
global configuration options.
"""


class GatenlpConfig:
    """ """

    def __init__(self):
        # The color to use for text in the generated viewer HTML for a document.#
        # So far this only applies to viewers where notebook=True
        self.doc_html_repr_txtcolor = "black"

        # set to True if the notebook has been initialized with the javascript needed by
        # the html-ann-viewer
        self.notebook_js_initialized = False

        # The height to use for row1/row2 and row1 if stretch_height is True
        self.doc_html_repr_height1_stretch = "height: 67vh;"
        self.doc_html_repr_height2_stretch = "height: 30vh;"

        # The height to use for row1/row2 and row1 if stretch_height is False
        self.doc_html_repr_height1_nostretch = "max-height: 20em;"
        self.doc_html_repr_height2_nostretch = "max-height: 14em;"

        # If string, use this as the default style for the document text
        self.doc_html_repr_doc_style = None

gatenlpconfig = GatenlpConfig()
