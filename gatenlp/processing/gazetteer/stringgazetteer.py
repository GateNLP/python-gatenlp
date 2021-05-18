"""
This module provides Gazetteer classes which allow matching the text or the tokens of documents against
gazetteer lists, lists of interesting texts or token sequences and annotate the matches with features from the
gazetteer lists.
"""

from recordclass import structclass
from gatenlp.utils import init_logger
from gatenlp.processing.gazetteer.base import GazetteerAnnotator


# TODO: Implement the StringGazetteer!!!!!!!!!!!!!!!!!!!!!!

# NOTE: Match was a dataclass originally
Match = structclass("Match", ("start", "end", "match", "entrydata", "matcherdata"))


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
        # TODO: need to figure out how to handle matching spaces vs. different spaces / no spaces!
        # self.nodes = defaultdict(Node)
        self.ignorefunc = ignorefunc
        self.mapfunc = mapfunc
        self.defaultdata = defaultdata
        self.matcherdata = matcherdata
        self._root = _Node()
        self.logger = init_logger(__name__)
        raise Exception("Not yet implemented")

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

    def find(
        self, text, all=False, skip=True, fromidx=None, toidx=None, matchmaker=None
    ):
        """
        Find gazetteer entries in text.
        ignored.
        :param text: string to search
        :param all: return all matches, if False only return longest match
        :param skip: skip forward over longest match (do not return contained/overlapping matches)
        :param fromidx: index where to start finding in tokens
        :param toidx: index where to stop finding in tokens (this is the last index actually used)
        :return: an iterable of Match. The start/end fields of each Match are the character offsets if
        text is a string, otherwise are the token offsets.
        """
        matches = []
        lentext = len(text)
        if fromidx is None:
            fromidx = 0
        if toidx is None:
            toidx = lentext - 1
        if fromidx >= lentext:
            return matches
        if toidx >= lentext:
            toidx = lentext - 1
        if fromidx > toidx:
            return matches
        i = fromidx
        self.logger.debug(f"From index {i} to index {toidx} for {text}")
        while i < toidx:
            chr = text[i]
            if self.ignorefunc and self.ignorefunc(chr):
                i += 1
                continue
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
                    if matchmaker:
                        match = matchmaker(
                            i,
                            i + k + 1,
                            text[i: i + k + 1],
                            node.value,
                            self.matcherdata,
                        )
                    else:
                        match = Match(
                            i,
                            i + k + 1,
                            text[i: i + k + 1],
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
                while True:
                    k += 1
                    if i + k >= len(text):
                        break
                    chr = text[i + k]
                    if self.ignorefunc and self.ignorefunc(chr):
                        continue
                    if self.mapfunc:
                        chr = self.mapfunc(chr)
                    node = node.children.get(chr)
                    break
                if i + k >= len(text):
                    break
            if not all and longest_match is not None:
                matches.append(longest_match)
            if skip:
                i += max(k, 1)
            else:
                i += 1
        return matches

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
