"""
Module that defines the CorpusViewer for browsing a corpus in a notebook.
"""
import ipywidgets as widgets
from ipywidgets import Button, HBox
from IPython.display import display, clear_output, HTML


class CorpusViewer:
    """
    Browse a corpus in a notebook. Note: for this the gatenlp "notebook" extra must be
    installed (e.g. pip install gatenlp[notebook])
    """
    def __init__(self, corpus, **kwargs):
        """
        Initialize a corpus viewer.

        Args:
            corpus: the corpus the view
            kwargs: parameters to pass on to the Document.show() method
        """
        self.corpus = corpus
        self.kwargs = kwargs
        layout = widgets.Layout(width="5em")
        self.bfwd = Button(icon='arrow-right', layout=layout)
        self.sldr = widgets.IntSlider(
            value=0, min=0, max=len(self.corpus)-1, step=1, readout=False)
        self.sldr.observe(self.show_for_sldr, names="value")
        self.bbck = widgets.Button(icon='arrow-left', layout=layout)
        self.label = widgets.Label(value="")
        self.bsync = widgets.Button(icon="refresh", layout=layout)
        self.bfwd.on_click(self.show_next)
        self.bbck.on_click(self.show_prev)
        self.bsync.on_click(lambda x: self.show())
        if len(self.corpus) == 0:
            raise Exception("Cannot show an empty corpus")
        self.idx = 0

    def show_for_sldr(self, info):
        self.idx = info["new"]
        self.show()

    def show(self, idx=None):
        if idx is not None:
            idx = idx-1
            self.idx = min(max(idx, 0), len(self.corpus)-1)
        doc = self.corpus[self.idx]
        self.sldr.value = self.idx
        clear_output()
        self.label.value = f"  {self.idx+1} / {len(self.corpus)}"
        display(HBox([self.bbck, self.sldr, self.bfwd, self.label, self.bsync]))
        doc.show(**self.kwargs)

    def show_next(self, _button):
        self.idx = min(self.idx+1, len(self.corpus)-1)
        self.show()

    def show_prev(self, _button):
        self.idx = max(self.idx-1, 0)
        self.show()
