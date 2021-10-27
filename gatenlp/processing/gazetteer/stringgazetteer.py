"""
This module provides Gazetteer classes which allow matching the text or the tokens of documents against
gazetteer lists, lists of interesting texts or token sequences and annotate the matches with features from the
gazetteer lists.
"""

from recordclass import structclass
from gatenlp.utils import init_logger
from gatenlp.processing.gazetteer.base import GazetteerAnnotator


# TODO: Implement the StringGazetteer!!!!!!!!!!!!!!!!!!!!!!
# TODO: Implement method that checks if we have a word start boundary before the current position, another for
#    a wird end boundary after the current position (default: whitespace or begin/end of doc)


# NOTE: sthis was a dataclass originally
StringGazetteerMatch = structclass(
    "StringGazetteerMatch", ("start", "end", "match", "data", "listidx")
)


_NOVALUE = object()

import sys


class _Node:
    """
    Trie Node: represents the value and the children.
    """

    __slots__ = ("children", "value")

    def __init__(self):
        self.children = dict()
        self.value = _NOVALUE

    # Will get removed or replaced with a proper pretty-printer!
    def debug_print_node(self, file=sys.stderr):
        if self.value == _NOVALUE:
            print("Node(val=,children=[", end="", file=file)
        else:
            print(f"Node(val={self.value},children=[", end="", file=file)
        for c, n in self.children.items():
            print(f"{c}:", end="", file=file)
            n.print_node()
        print("])", end="", file=file)


class StringGazetteer(GazetteerAnnotator):
    def __init__(
        self, ignorefunc=None, mapfunc=None, matcherdata=None, defaultdata=None
    ):
        """
        NOTE: NOT YET IMPLEMENTED! (code copied from Matcher package, mostly unchanges)

        Create a String Gazetteer.

        Args:
            ignorefunc: a predicate that returns True for any token that should be ignored.
            mapfunc: a function that returns the string to use for each token.
            matcherdata: data to add to all matches in the matcherdata field
            defaultdata: data to add to matches when the entry data is None
        """
        # TODO: need to figure out how to handle word boundaries
        #     Maybe the easiest way: optionally limit the start and end of a match to a list of offsets
        #     That list of offsets can be determined by either the offsets from annotations or by running
        #     something that e.g. looks for whitespace first
        # TODO: need to figure out how to handle matching spaces vs. different spaces / no spaces!
        #     Basically, certain characters in the entry can be defined to match a varying number of
        #     characters in the text, e.g. a single space could match one or more spaces in the text
        # TODO: need to figure out how to terminate matches, e.g. provide a list of offsets where any
        #     match will be interrupted (e.g. split tokens).
        # TODO: maybe make the ignorefunc, mapfunc etc. more flexible by always passing the character and the offset
        #     that way we could implement something that pre-processes the document to e.g. get offsets where
        #     we simply ignore. This would also allow for using a SPLITFUNC which returns true (abort match) either
        #     when we find a Newline or we are at the offset where we have a split annotation
        # self.nodes = defaultdict(Node)
        self.ignorefunc = ignorefunc
        self.mapfunc = mapfunc
        self.defaultdata = defaultdata
        self.matcherdata = matcherdata
        self._root = _Node()
        self.logger = init_logger(__name__)

    def add(self, entry, data=None, listdata=None, append=False):
        """
        Add a gazetteer entry or several entries if "entry" is iterable and not a string and store its data.
        Note that data has to be a non-None value to indicate that this entry is in the tree (e.g. True).

        If an entry already exists, the data is replaced with the new data unless append is True
        in which case the data is appended to the list of data already there.

        If all elements of the entry are ignored, nothing is done.

        :param entry: a string
        :param data: the data to add for that gazetteer entry.
        :param listdata: the list data to add for that gazeteer entry.
        :param append: if true and data is not None, store data in a list and append any new data
        :return:
        """
        if isinstance(entry, str):
            entry = [entry]
        for e in entry:
            node = self._get_node(e, create=True)
            if node == self._root:
                # empty string not allowed
                continue
            if node.value == _NOVALUE:
                if append:
                    node.value = [data]
                else:
                    node.value = data
            else:
                if append:
                    node.value.append(data)
                else:
                    node.value = data

    def match(self, text, all=False, start=0, end=None, matchfunc=None):
        """
        Try to start at offset start in text, if end is not None, do not match beyond end offset.

        Args:
            text: the text/string in which to find matches
            all:  if True, return all matches, otherwise return only the longest matches. If None, uses the setting
                from init.
            start: the offset where the match must start
            end: if not None, the offset beyond which a match is not allowed to end
            matchfunc: NOT YET USED

        Returns:
            A tuple where the first element is a list of match objects and the second the length of the longest match,
            0 if there is no match (list of match objects is empty)

        """
        matches = []
        lentext = len(text)
        if start is None:
            start = 0
        if end is None:
            end = lentext - 1
        if start >= lentext:
            return matches, 0
        if end >= lentext:
            end = lentext - 1
        if start > end:
            return matches, 0
        self.logger.debug(f"Trying to match at offset {start} to at most index {end} for {text}")
        chr = text[start]
        if self.ignorefunc:
            while self.ignorefunc(chr):
                start += 1
                chr = text[start]
                if start >= end:
                    return matches, 0
        if self.mapfunc:
            chr = self.mapfunc(chr)
        longest_len = 0
        longest_match = None
        node = self._root
        node = node.children.get(chr)
        k = 0
        while node is not None:
            if node.value != _NOVALUE:
                # we found a match
                cur_len = k + 1
                match = StringGazetteerMatch(
                    start,
                    start + k + 1,
                    text[start: start + k + 1],
                    node.value,
                    self.matcherdata,
                )
                if all:
                    matches.append(match)
                else:
                    # NOTE: only one longest match is possible, but it can have a list of data if append=True
                    if cur_len > longest_len:
                        longest_len = cur_len
                        longest_match = match
            if not all and longest_match is not None:
                matches.append(longest_match)
        return matches, longest_len



    # TODO: implement in terms of match
    def find(
        self, text, all=False, skip=True, start=None, end=None, matchmaker=None,
    ):
        """
        Find gazetteer entries in text.
        ignored.

        Args:
            text: string to search
            all: return all matches, if False only return longest match
            skip: skip forward over longest match (do not return contained/overlapping matches)
            start: offset where to start matching in the text
            end: of not None, offset beyond which no match may happen (start or end)

        Returns:
             NOT SURE YET???
        """
        if all is None:
            all = self.all
        offset = start
        if end is None:
            end = len(text) - 1
        while offset <= end:
            matches, long = self.match(
                text, all=all, start=offset, end=end,
            )
            if long == 0:
                offset += 1
                continue
            return matches, long, offset
        return [], 0, None

    def find_all(self):
        pass

    def __setitem__(self, key, value):
        node = self._get_node(key, create=True)
        node.value = value

    def __getitem__(self, item):
        node = self._get_node(item, create=False, raise_error=True)
        if node.value == _NOVALUE:
            raise KeyError(item)
        return node.value

    def get(self, item, default=None):
        node = self._get_node(item, create=False, raise_error=False)
        if node is None:
            return default
        if node.value == _NOVALUE:
            return default
        return node.value

    def _get_node(self, item, create=False, raise_error=True):
        """
        Returns the node corresponding to the last character in key or raises a KeyError if create is False
        and the node does not exist. If create is True, inserts the node.

        :param item: the key for which to find a node
        :param create: if True, insert all necessary nodes
        :param raise_error: if True and create is False, raises an error if not found, if False, returns None
        :return: the node corresponding to the key or None if no node found and raise_error is False
        """
        node = self._root
        for el in item:
            if self.ignorefunc and self.ignorefunc(el):
                continue
            if self.mapfunc:
                el = self.mapfunc(el)
            if create:
                node = node.children.setdefault(el, _Node())
            else:
                node = node.children.get(el)
                if not node:
                    if raise_error:
                        raise KeyError(item)
                    else:
                        return None
        return node
