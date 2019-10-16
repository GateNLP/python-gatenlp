__version__ = "0.1"

# this attribute globally holds the processing resource last defined
# so it can be used for interacting with the GATE python plugin
from gatenlp.gate_interaction import _pr_decorator as PR
from gatenlp.gate_interaction import interact
from gatenlp.annotation import Annotation
from gatenlp.document import Document
from gatenlp.annotation_set import AnnotationSet
from gatenlp.exceptions import InvalidOffsetException
from gatenlp.changelog import ChangeLog

__all__ = ["PR", "Annotation", "Document", "AnnotationSet",
           "InvalidOffsetException", "ChangeLog"]

gate_python_plugin_pr = None

