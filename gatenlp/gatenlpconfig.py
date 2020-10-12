

class GatenlpConfig:
    def __init__(self):
        # If True, add the javascript to the generated HTML so we do not depend on an
        # internet connection for the HTML to work.
        self.doc_html_repr_offline = False


gatenlpconfig = GatenlpConfig()
