from collections.abc import Iterable
import inspect
from gatenlp.processing.annotator import Annotator


def _check_and_ret_callable(a, **kwargs):
    """
    Make sure a is either a callable or a class that can be instatiated to a callable.

    :param a: a class or instantiated callable
    :param kwargs: arguments to pass on to the initializer
    :return: an instantiated callable or throws an exception if not a callable
    """
    if inspect.isclass(a):
        a = a(**kwargs)
    if not callable(a):
        raise Exception(f"Not a callable: {a}")
    return a

def _has_method(obj, name):
    """
    Check if the object has a method with that name

    :param obj: the object
    :param name: the name of the method
    :return: True if the object has a callable method with that name, otherwise False
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
    """

    def __init(self, *annotators, **kwargs):
        """

        :param annotators: each paramter can be an annotator or callable, if it is an iterable,
           it is assumed to be an iterable of callables or lists. If it is not an iterable, it can
           be either a class or an already initialized instance of a class which must be a callable
           or some other callable.
        :param kwargs:
        :return:
        """
        self.annotators = []
        for ann in annotators:
            if isinstance(ann, Iterable):
                for a in ann:
                    a = _check_and_ret_callable(a)
                    self.annotators.append(a)
            else:
                a = _check_and_ret_callable(a)
                self.annotators.append(ann)

    def __call__(self, doc, **kwargs):
        """
        Calls each annotator in sequence and passes the result or results to the next.

        :param doc: the document to process
        :param kwargs:
        :return: a document or a list of documents
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
        Invoke start on all annotators to prepare them for a corpus of documents.

        :return:
        """
        for annotator in self.annotators:
            if _has_method(annotator, "start"):
                annotator.start()

    def finish(self):
        """
        Invoke finish on all annotators and return their results as a list with as many
        elements as there are annotators (annotators which did not return anything have None).

        :return: list of annotator results
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
        Invoke reduce on all annotators using the list of result lists. `results` is a list with
        as many elements as there are annotators. Each element is a list of results from different
        processes or different batches.

        Returns a list with as many elements as there are annotators, each element the combined result.

        :param results: a list of result lists
        :return: a list of combined results
        """
        results = []
        assert len(results) == len(self.annotators)
        for reslist, annotator in zip(results, self.annotators):
            if _has_method(annotator, "reduce"):
                results.append(annotator.reduce(reslist))
            else:
                results.append(reslist)
        return results

