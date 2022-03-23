
import ipywidgets as widgets
from ipywidgets import Button, HBox, VBox
from IPython.display import display, clear_output

from gatenlp import Document
from gatenlp.corpora import DirFilesCorpus


class CorpusViewer:

    def __init__(self, corpus, **kwargs):
        self.corpus = corpus
        self.kwargs = kwargs
        layout = widgets.Layout(width="5em")
        self.bfwd = Button(icon='arrow-right', layout=layout)
        self.sldr = widgets.IntSlider(
            value=0,min=0,max=len(self.corpus)-1,step=1,readout=False)
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

    def show(self):
        clear_output()
        doc = self.corpus[self.idx]
        self.label.value = f"  {self.idx+1} / {len(self.corpus)}"
        display(HBox([self.bbck, self.sldr, self.bfwd, self.label, self.bsync]))
        doc.show(**self.kwargs)

    def show_next(self, button):
        self.idx = min(self.idx+1, len(self.corpus)-1)
        self.show()

    def show_prev(self, button):
        self.idx = max(self.idx-1, 0)
        self.show()