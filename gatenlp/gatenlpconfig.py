"""
Module that provides the class GatenlpConfig and the instance gatenlpconfig which stores various
global configuration options.
"""

class GatenlpConfig:
    """ """
    def __init__(self):
        # If True, add the javascript to the generated HTML so we do not depend on an
        # internet connection for the HTML to work.
        self.doc_html_repr_offline = False
        # The color to use for text in the generated viewer HTML for a document.#
        # So far this only applies to viewers where notebook=True
        self.doc_html_repr_txtcolor = "black"


gatenlpconfig = GatenlpConfig()
