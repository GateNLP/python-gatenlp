"""
Various internal small utility functions needed by other modules.
"""

import numbers
from functools import wraps

def support_annotation_or_set(method):
    """
    Decorator to allow a method that normally takes a start and end
    offset to take an annotation or annotation set, or any other object that has
    "start" and "end" attributes, or a pair of offsets instead.
    It also allows to take a single offset instead which will then be used as both start and end offset.
    """
    @wraps(method)
    def _support_annotation_or_set(self, *args):
        if len(args) == 1:
            obj = args[0]
            if hasattr(obj, "start") and hasattr(obj, "end"):
                left, right = obj.start, obj.end
            elif isinstance(obj, (tuple, list)) and len(obj) == 2:
                left, right = obj
            elif isinstance(obj, numbers.Integral):
                left, right = obj, obj+1
            else:
                raise Exception("Not an annotation or an annotation set or pair: {}".format(args[0]))
        else:
            assert len(args) == 2
            left, right = args

        return method(self, left, right)

    return _support_annotation_or_set

