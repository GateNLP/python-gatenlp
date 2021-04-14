#!/usr/bin/env python
"""
Module for interacting with a Java GATE process.
"""

from gatenlp.urlfileutils import is_url
from gatenlp.processing.annotator import Annotator

# NOTE: we delay importing py4j to the class initializer. This allows us to make GateWorker available via gatenlp
# but does not force everyone to actually have py4j installed if they do not use the GateWorker
# from py4j.java_gateway import JavaGateway, GatewayParameters
from gatenlp.utils import init_logger

logger = init_logger("gateworker-annotator")


class GateWorkerAnnotator(Annotator):   # pragma: no cover
    # TODO: parameter to influence how exceptions are handled
    def __init__(
            self,
            pipeline,
            gateworker,
            annsets_send=None,
            annsets_receive=None,
            replace_anns=False,
            update_document=False,
    ):
        """
        Create a GateWorker annotator.

        This starts the gate worker, loads the pipeline and
        can then be used to annotate Python gatenlp Document instances with the Java GATE
        pipeline.

        Note: to make sure that start/finish callbacks on the Java side are invoked, the annotator
        start() method should be invoked once before processing documents and finish() should
        get called once after processing documents. (Any Executor implementation shoudl do this
        autimatically)

        If the GateWorkerAnnotator is not used any more, close() should be invoked to terminate
        the Java GATE Worker process.

        Example:

            ```python
            pipeline = GateWorkerAnnotator("annie.xgapp", GateWorker())
            for idx, doc in enumerate(mycorpus):
                corpus[idx] = pipeline(doc)
            ```

        Args:
            pipeline: the path to a Java GATE pipeline to load into the GATE worker
            gateworker: the gate home directory to use, if not set, uses environment variable GATE_HOME
            annsets_send: a list of either annotation set names, or tuples where the first element
                is the name of an annotation set and the second element is either the name of a type
                or a list of type names. If not None, only the sets/types specified are sent to Java GATE.
                If an empty list is specified, no annotations are sent at all.
            annsets_receive: this only works if update_document is True: same format as annsets_send to specify
                which annotation sets/types are
                sent back to Python after the document has been processed on the Java side.
            replace_anns: this is only relevant if update_document is True: if True and an annotation is received
                which already exists (same set and annotation id)
                then the existing annotation is replaced (if offsets and type are also same, only the features are
                replaced). If False, all received annotations are added which may change their annotation id.
            update_document: if True, then existing annotations in the gatenlp document are kept and the annotations
                received from Java GATE are added. In this case, other changes to the document, e.g. the document
                text or document features are not applied to the current python document.
                If False, the existing document is completely replaced with what gets
                received from Java GATE.
        """
        self.pipeline = pipeline
        self.annsets_send = annsets_send
        self.annsets_receive = annsets_receive
        self.replace_anns = replace_anns
        self.update_document = update_document
        self.gateworker = gateworker
        isurl, ext = is_url(pipeline)
        if isurl:
            self.controller = self.gateworker.worker.loadPipelineFromUri(ext)
        else:
            self.controller = self.gateworker.worker.loadPipelineFromFile(ext)
        self.corpus = self.gateworker.worker.newCorpus()
        self.controller.setCorpus(self.corpus)
        self.controller.setControllerCallbacksEnabled(False)

    def start(self):
        """
        Invoke the controller execution started method on the GATE controller.
        """
        self.controller.invokeControllerExecutionStarted()

    def finish(self):
        """
        Invoke the controller execution finished method on the GATE controller.
        """
        self.controller.invokeControllerExecutionFinished()

    def __call__(self, doc, **_kwargs):
        """
        Run the GATE controller on the given document.

        This runs the GATE pipeline (controller) on the given document by first sending the document
        to the GATE process and coverting it to a GATE document there, running the pipeline on it,
        and sending the document back and converting back to a new gatenlp Document.

        Args:
            doc: the document to process
            **kwargs: ignored so far

        Returns:
            the processed gatenlp document
        """
        if self.annsets_send is not None:
            # create shallow copy, we only need it for reading!
            tmpdoc = doc.copy(annsets=self.annsets_send)
        else:
            tmpdoc = doc
        gdoc = self.gateworker.pdoc2gdoc(tmpdoc)
        self.gateworker.worker.run4Document(self.controller, gdoc)
        if self.update_document:
            self.gateworker.gdocanns2pdoc(gdoc, doc, annsets=self.annsets_receive, replace=self.replace_anns)
        else:
            doc = self.gateworker.gdoc2pdoc(gdoc)
        self.gateworker.del_resource(gdoc)
        return doc
