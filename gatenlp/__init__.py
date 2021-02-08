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
from gatenlp.gateworker import GateWorker, GateWorkerAnnotator
from gatenlp.gate_interaction import _pr_decorator as GateNlpPr
from gatenlp.gate_interaction import interact


def init_notebook():
    from gatenlp.serialization.default import HtmlAnnViewerSerializer
    from gatenlp.gatenlpconfig import gatenlpconfig

    HtmlAnnViewerSerializer.init_javscript()
    gatenlpconfig.notebook_js_initialized = True
