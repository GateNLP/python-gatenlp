# NOTE: do not place a comment at the end of the version assignment
# line since we parse that line in a shell script!
__version__ = "0.7"
import logging
try:
    import sortedcontainers
except Exception as ex:
    import sys
    print("ERROR: required package sortedcontainers cannot be imported!", file=sys.stderr)
    print("Please install it, using e.g. 'pip install -U sortedcontainers'", file=sys.stderr)
    sys.exit(1)
# TODO: check version of sortedcontainers (we have 2.1.0)
logging.basicConfig()
logger = logging.getLogger("gatenlp")
logger.setLevel(logging.INFO)

# this attribute globally holds the processing resource last defined
# so it can be used for interacting with the GATE python plugin
from gatenlp.gate_interaction import _pr_decorator as GateNlpPr
from gatenlp.gate_interaction import interact
from gatenlp.annotation import Annotation
from gatenlp.document import Document
from gatenlp.annotation_set import AnnotationSet
from gatenlp.exceptions import InvalidOffsetException
from gatenlp.changelog import ChangeLog
# from gatenlp.gateslave import GateSlave

__all__ = ["GateNlpPr", "Annotation", "Document", "AnnotationSet",
           "InvalidOffsetException", "ChangeLog", "logger"]

gate_python_plugin_pr = None

