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


gatenlpconfig = GatenlpConfig()
