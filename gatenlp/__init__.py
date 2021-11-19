"""
The following classes are imported into the gatenlp package by default: `gatenlp.span.Span`,
`gatenlp.annotation.Annotation`,
`gatenlp.annotation_set.AnnotationSet`, `gatenlp.changelog.ChangeLog`, `gatenlp.document.Document` as well
as `GateNlpPr` and `interact` for the GATE Python plugin.

Where to find other important classes:

* corpora, document sources, document destinations: in `gatenlp.corpora`
* `gatenlp.gateworker.gateworker.GateWorker`, `gatenlp.gateworker.gateworkerannotator.GateWorkerAnnotator`
   in `gatenlp.gateworker`
* `gatenlp.lib_spacy.AnnSpacy` in `gatenlp.lib_spacy`
* `gatenlp.lib_stanza.AnnStanza` in `gatenlp.lib_stanza`
* TODO: include all the others!
"""

# NOTE: do not place a comment at the end of the version assignment
# line since we parse that line in a shell script!
# __version__ = "0.9.9"
from gatenlp.version import __version__

try:
    import sortedcontainers
except Exception:
    import sys
    print(
        "ERROR: required package sortedcontainers cannot be imported!", file=sys.stderr
    )
    print(
        "Please install it, using e.g. 'pip install -U sortedcontainers'",
        file=sys.stderr,
    )
    sys.exit(1)
# TODO: check version of sortedcontainers (we have 2.1.0)

from gatenlp.utils import init_logger

logger = init_logger("gatenlp")
from gatenlp.span import Span
from gatenlp.annotation import Annotation
from gatenlp.annotation_set import AnnotationSet
from gatenlp.changelog import ChangeLog
from gatenlp.document import Document
from gatenlp.gate_interaction import _pr_decorator as GateNlpPr
from gatenlp.gate_interaction import interact

# Importing GateWorker or other classes which depend on any package other than sortedcontains will
# break the Python plugin!
# from gatenlp.gateworker import GateWorker, GateWorkerAnnotator


def init_notebook():   # pragma: no cover
    """
    Helper method to initialize a Jupyter or similar notebook.
    """
    from gatenlp.serialization.default import HtmlAnnViewerSerializer
    from gatenlp.gatenlpconfig import gatenlpconfig

    HtmlAnnViewerSerializer.init_javscript()
    gatenlpconfig.notebook_js_initialized = True
