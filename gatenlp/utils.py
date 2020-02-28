"""
Various utilities that could be useful in several modules.
"""


def to_dict(obj):
    """
    If obj is not None, call its to_dict method, otherwise return None
    :param obj: the object on which to call to_dict
    :return: the result of to_dict or None
    """
    if obj is None:
        return None
    else:
        return obj.to_dict()


def to_list(obj):
    """
    If obj is not None, call its to_list method, otherwise return None
    :param obj: the object on which to call to_list
    :return: the result of to_list or None
    """
    if obj is None:
        return None
    else:
        return obj.to_list()


def match_substrings(text, items, getstr=None, cmp=None, unmatched=False):
    """
    Matches each item from the items sequence with sum substring of the text
    in a greedy fashion. An item is either already a string or getstr is used
    to retrieve a string from it. The text and substrings are normally
    compared with normal string equality but cmp can be replaced with
    a two-argument function that does the comparison instead.
    This function expects that all items are present in the text, in their order
    and without overlapping! If this is not the case, an exception is raised.

    :param text: the text to use for matching
    :param items: items that are or contains substrings to match
    :param getstr: a function that retrieves the text from an item
    :param cmp: a function that compares to strings and returns a boolean \
    that indicates if they should be considered to be equal.
    :param unmatched: if true returns two lists of tuples, where the second list\
    contains the offsets of text not matched by the items
    :return: a list of tuples (start, end, item) where start and end are the\
    start and end offsets of a substring in the text and item is the item for that substring.
    """
    if getstr is None:
        getstr = lambda x: x
    if cmp is None:
        cmp = lambda x,y: x == y
    ltxt = len(text)
    ret = []
    ret2 = []
    item_idx = 0
    start = 0
    lastunmatched = 0
    while start < ltxt:
        itemorig = items[item_idx]
        item = getstr(itemorig)
        end = start + len(item)
        if end > ltxt:
            raise Exception("Text too short to match next item: {}".format(item))
        if cmp(text[start:end], item):
            if unmatched and start > lastunmatched:
                ret2.append((lastunmatched, start))
                lastunmatched = start + len(item)
            ret.append((start, end, itemorig))
            start += len(item)
            item_idx += 1
            if item_idx == len(items):
                break
        else:
            start += 1
    if item_idx != len(items):
        raise Exception("Not all items matched but {} of {}".format(item_idx, len(items)))
    if unmatched and lastunmatched != ltxt:
        ret2.append((lastunmatched, ltxt))
    if unmatched:
        return ret, ret2
    else:
        return ret


