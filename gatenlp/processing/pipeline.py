"""
Module that provides the Pipeline class. A Pipeline is an annotator which is configured to contain several annotators
which get executed in sequence. The result of each annotator is passed on to the next anotator.
Each annotator can return a single document, None, or list of documents. If no document is returned, subsequent
annotators are not called and None is returned from the pipeline. If several documents are areturned, subsequent
annotators are invoked for each of those documents and the list of final return documents is returned by the pipeline.

Whenever a single document is returned it is returned as the document and NOT as a list with a single document as
the only element.
"""

from collections.abc import Iterable
import inspect
from gatenlp.processing.annotator import Annotator
from gatenlp.utils import init_logger


def _check_and_ret_callable(a, **kwargs):
    """
    Make sure a is either a callable or a class that can be instatiated to a callable.

    Args:
      a: a class or instantiated callable
      kwargs: arguments to pass on to the initializer
      **kwargs:

    Returns:
        an instantiated callable or throws an exception if not a callable

    """
    if inspect.isclass(a):
        a = a(**kwargs)
    if not callable(a):
        raise Exception(f"Not a callable: {a}")
    return a


def _has_method(obj, name):
    """
    Check if the object has a method with that name

    Args:
      obj: the object
      name: the name of the method

    Returns:
        True if the object has a callable method with that name, otherwise False

    """
    mth = getattr(obj, name, None)
    if mth is None:
        return False
    elif callable(mth):
        return True
    else:
        return False


class Pipeline(Annotator):
    """
    A pipeline is an annotator which runs several other annotators in sequence on a document
    and returns the result. Since annotators can return no or more than one result document
    in a list, the pipeline can return no or more than one document for each input document
    as well.

    When the start/finish/reduce method of the pipeline is invoked, all start/finish/reduce methods of
    all annotators are invoked in sequence. The finish method returns the list of all return values of
    all the finish methods of the annotators (if a finish method returns None, this is added to the list).

    The reduce method expects a list with as many return value lists as there are annotators and returns
    the overall result for each annotator (again, including None if there is none).
    """

    def __init__(self, *annotators, **kwargs):
        """
        Creates a pipeline annotator.

        Args:
            annotators: each parameter can be an annotator or callable, if it is an iterable,
                it is assumed to be an iterable of callables or lists. If it is not an iterable, it can
                be either a class or an already initialized instance of a class which must be a callable
                or some other callable.
            **kwargs: these arguments are passed to the constructor of any class in the annotators list
        """
        self.annotators = []
        self.logger = init_logger(__name__)
        for ann in annotators:
            if isinstance(ann, Iterable):
                for a in ann:
                    a = _check_and_ret_callable(a)
                    self.annotators.append(a)
            else:
                a = _check_and_ret_callable(a, **kwargs)
                self.annotators.append(ann)
        if len(self.annotators) == 0:
            self.logger.warn("Pipeline is a do-nothing pipeline: no annotators")

    def __call__(self, doc, **kwargs):
        """
        Calls each annotator in sequence and passes the result or results to the next.

        Args:
            doc: the document to process
            **kwargs: any kwargs will be passed to all annotators

        Returns:
            a document or a list of documents
        """
        toprocess = [doc]
        results = []
        for annotator in self.annotators:
            results = []
            for d in toprocess:
                ret = annotator(doc, **kwargs)
                if isinstance(ret, list):
                    results.extend(ret)
                else:
                    if ret is not None:
                        results.append(ret)
            toprocess = results
        if len(results) == 1:
            return results[0]
        else:
            return results

    def start(self):
        """
        Invokes start on all annotators.
        """
        for annotator in self.annotators:
            if _has_method(annotator, "start"):
                annotator.start()

    def finish(self):
        """
        Invokes finish on all annotators and return their results as a list with as many
        elements as there are annotators (annotators which did not return anything have None).

        Returns:
            list of annotator results
        """
        results = []
        for annotator in self.annotators:
            if _has_method(annotator, "finish"):
                results.append(annotator.finish())
            else:
                results.append(None)
        return results

    def reduce(self, results):
        """
        Invokes reduce on all annotators using the list of result lists. `results` is a list with
        as many elements as there are annotators. Each element is a list of results from different
        processes or different batches.

        Returns a list with as many elements as there are annotators, each element the combined result.

        Args:
            results: a list of result lists

        Returns:
            a list of combined results
        """
        results = []
        assert len(results) == len(self.annotators)
        for reslist, annotator in zip(results, self.annotators):
            if _has_method(annotator, "reduce"):
                results.append(annotator.reduce(reslist))
            else:
                results.append(reslist)
        return results
