"""
This module provides Gazetteer classes which allow matching the text or the tokens of documents against
gazetteer lists, lists of interesting texts or token sequences and annotate the matches with features from the
gazetteer lists.
"""

from collections import defaultdict
from dataclasses import dataclass
from gatenlp.utils import ensurelogger
from gatenlp.processing.annotator import Annotator


class Gazetteer(Annotator):
    """
    Base class of all gazetteer classes.
    """
    pass


@dataclass(unsafe_hash=True, order=True)
class TokenGazetteerMatch:
    __slots__ = ("start", "end", "match", "entrydata", "matcherdata")
    start: int
    end: int
    match: list
    entrydata: object
    matcherdata: object


class TokenGazetteerNode(object):
    """
    Represent an entry in the hash map of entry first tokens.
    If is_match is True, that token is already a match and data contains the entry data.
    The continuations attribute contains None or a list of multi token matches that
    start with the first token and the entry data if we have a match (all tokens match).
    """
    __slots__ = ("is_match", "data", "nodes", "listidx")

    def __init__(self, is_match=None, data=None, nodes=None, listidx=None):
        """

        Args:
            is_match: this node is a match
            data: data associated with the match, can be a list of data items
            nodes:
            listidx: list index or list of list indices for the list data this item refers to
        """
        self.is_match = is_match
        self.data = data
        self.listidx = listidx
        self.nodes = nodes

    @staticmethod
    def dict_repr(nodes):
        if nodes is not None:
            return str([(t, n) for t, n in nodes.items()])

    def __repr__(self):
        nodes = TokenGazetteerNode.dict_repr(self.nodes)
        return f"Node(is_match={self.is_match},data={self.data},nodes={nodes})"


class TokenGazetteer:

    def __init__(self,
                 source,
                 fmt="gate-def",
                 feature=None,
                 setname="",
                 tokentype="Token",
                 septype=None,
                 splittype=None,
                 withintype=None,
                 mapfunc=None,
                 ignorefunc=None,
                 getterfunc=None,
                 listfeatures=None,
                 matcherfeatures=None,
                 append=True,
                 ):
        """

        Args:
            source: where to load the gazetteer from. What is actually expected here depends on the fmt
              parameter.
            fmt: defines what is expected as the format and/or content of the source parameter. One of:
               *  "gate-def" (default): source must be a string, a pathlib Path or a parsed urllib url and
                  point to a GATE-style "def" file. See https://gate.ac.uk/userguide/chap:gazetteers
               * "gazlist": a list of tuples or lists where the first element of the tuple/list
                  is a list of strings, the second element is a dictionary containing the features to assign and
                  the third element, if it exists, is the index of an element in the listfeatures array.
            feature: the feature name to use to get the string for each token. If the feature does not exist, is None
              or is the empty string, the Token is completely ignored. If the feature name is None, use the document
              string covered by the token.
            setname: the set where the tokens to match should come from
            tokentype: the annotation type of the token annotations
            septype: the annotation type of separator annotations (NOT YET USED)
            splittype: the annotation type of any split annotations which will end any ongoing match
            withintype: only matches fully within annotations of this type will be made
            listfeatures: a list of dictionaries containing the features to set for all matches witch have the
              list index set.
            mapfunc: a function that maps the original string extracted for each token to the actual string to use.
            ignorefunc: a function which given the mapped token string decides if the token should be ignored
              (not added to the gazetteer list, not considered in the document when matching)
            getterfunc: a function which, given a token annotation, retrieves the string. If there is mapfunc, the
              retrieved string is then still run through the mapfunc. The getterfunc must accept the token and
              an optional document as parameters
            append: if an entry occurs in the source which is already in the gazetteer, append the data so the
              gazetteer entry contains a list of a data (True), or replace the existing data with the new data (False)
        """
        self.nodes = defaultdict(TokenGazetteerNode)
        self.mapfunc = mapfunc
        self.ignorefunc = ignorefunc
        self.feature = feature
        if getterfunc:
            self.getterfunc = getterfunc
        else:
            if feature:
                self.getterfunc = lambda tok, doc=None: tok.features[feature]
            else:
                self.getterfunc = lambda tok, doc=None: doc[tok]
        self.listfeatures = listfeatures.copy()
        self.load(source, fmt=fmt, append=append)  # we just copied the listfeatures, do not pass!

    def load(self,
             source,
             fmt="gate-def",
             listfeatures=None,
             append=True
             ):
        """
        This method adds more entries to gazetteer. It works just like the constructor, but adds additional
        data into the gazetteer.

        Args:
            source: where to load the gazetteer from. What is actually expected here depends on the fmt
              parameter.
            fmt: defines what is expected as the format and/or content of the source parameter. One of:
               *  "gate-def" (default): source must be a string, a pathlib Path or a parsed urllib url and
                  point to a GATE-style "def" file. See https://gate.ac.uk/userguide/chap:gazetteers
               * "gazlist": a list of tuples or lists where the first element of the tuple/list
                  is a list of strings, the second element is a dictionary containing the features to assign and
                  the third element, if it exists, is the index of an element in the listfeatures array.
            listfeatures: a list of dictionaries containing the features to set for all matches witch have the
              list index set, this list gets appended to the existing listfeatures.
            append: if an entry occurs in the source which is already in the gazetteer, append the data so the
              gazetteer entry contains a list of a data (True), or replace the existing data with the new data (False)
        """
        if isinstance(listfeatures, list):
            if self.listfeatures is None:
                self.listfeatures = []
            self.listfeatures.extend(listfeatures)

        if fmt == "gazlist":
            for el in source:
                entry = el[0]
                data = el[1]
                if len(el) > 2:
                    listidx = el[2]
                else:
                    listidx = None
                self.add(entry, data, listidx=listidx, append=append)
        elif fmt == "gate-def":
            pass
        else:
            raise Exception(f"TokenGazetteer format {fmt} not known")

    def add(self, entry, data=None, append=True, listidx=None):
        """
        Add a single gazetteer entry. If the same entry already exsists, the new data is added to the entry unless
        append is False in which case the existing entry is replaced.

        Args:
            entry: a iterable of string or a string for a single element
            data: a dictionary of features to add to
            append: if true and data is not None, store data in a list and append any new data
            listidx: The index of a listfeatures entry to add to the entry.
        """
        if isinstance(entry, str):
            entry = [entry]
        node = None
        i = 0
        for token in entry:  # each "token" is a string or None, where None indicates a separator
            if self.mapfunc is not None:
                token = self.mapfunc(token)
            if self.ignorefunc is not None and self.ignorefunc(token):
                continue
            if i == 0:
                node = self.nodes[token]
            else:
                if node.nodes is None:
                    node.nodes = defaultdict(TokenGazetteerNode)
                    tmpnode = TokenGazetteerNode()
                    node.nodes[token] = tmpnode
                    node = tmpnode
                else:
                    node = node.nodes[token]
            i += 1
        node.is_match = True
        if data is not None:
            # we need to set or append
            if append:
                if node.data:
                    node.data.append(data)
                else:
                    node.data = [data]
            else:
                node.data = data
        if listidx is not None:
            if append:
                if node.listidx:
                    node.listidx.append(listidx)
                else:
                    node.listidx = [listidx]
            else:
                node.listidx = listidx

    def match(self, tokens, doc=None, all=False, idx=0, matchfunc=None):
        """
        Try to match at index location idx of the tokens sequence. If successful and all is False,
        return the match object or True or whatever matchfunc returns. If successful and all is True,
        return the list of match objects or True, or whatever the matchfunc returns.
        If unsuccessful return None.

        Args:
            tokens:
            doc:
            all:
            idx:
            matchfunc:

        Returns:

        """
        pass

    def find_next(self, tokens, doc=None, all=False, skip=True, fromidx=None, toidx=None, matchfunc=None):
        """
        Find the next match in the given index range and return None if no match found, or an indication
        of matching as for the `match` method.

        Args:
            tokens:
            doc:
            all:
            fromidx:
            toidx:
            matchfunc:

        Returns:

        """
        # if match:
        pass

    # TODO: try to implement find_all in terms of match/find_next
    def find_all(self, tokens, doc=None, all=False, skip=True, fromidx=None, toidx=None, matchfunc=None, reverse=True):
        """
        Find gazetteer entries in a sequence of tokens.
        Note: if fromidx or toidx are bigger than the length of the tokens allows, this is silently
        ignored.

        Args:
            tokens: iterable of tokens. The getter will be applied to each one and the doc to retrieve the initial
               string.
            doc: the document this should run on. Only necessary if the text to match is not retrieved from
               the token annotation, but from the underlying document text.
            all: return all matches, if False only return longest match
            skip: skip forward over longest match (do not return contained/overlapping matches)
            fromidx: index where to start finding in tokens
            toidx: index where to stop finding in tokens (this is the last index actually used)
            matchfunc: a function which takes the data from the gazetteer, the token and doc and performs
                some action. Signature should be (startoff, endoff, tokenlist, doc=None, data=None, listidxs=None)

        Returns:
            An iterable of Match if not matchfunc is specified, otherwise an iterable of what matchfunc
            returned for each match. The start/end fields of each Match are the token indices.
        """
        logger = ensurelogger()
        logger.debug("CALL")
        matches = []
        l = len(tokens)
        if fromidx is None:
            fromidx = 0
        if toidx is None:
            toidx = l-1
        if fromidx >= l:
            return matches
        if toidx >= l:
            toidx = l-1
        if fromidx > toidx:
            return matches
        i = fromidx
        logger.debug(f"From index {i} to index {toidx} for {tokens}")
        while i <= toidx:
            token_obj = tokens[i]
            token = self.getterfunc(token_obj)
            logger.debug(f"Check token {i}={token}")
            if self.mapfunc:
                token = self.mapfunc(token)
            if self.ignorefunc:
                if self.ignorefunc(token):
                    continue
            # check if we can match the current token
            if token in self.nodes:  # only possible if the token was not ignored!
                # ok, we have the beginning of a possible match
                longest = 0
                node = self.nodes[token]
                logger.debug(f"Got a first token match for {token}")
                thismatches = []
                thistokens = [token_obj]
                if node.is_match:
                    # the first token is already a complete match, so we need to add this to thismatches
                    logger.debug(f"First token match is also entry match")
                    longest = 1
                    # TODO: make this work with list data!
                    if matchfunc:
                        match = matchfunc(i, i+1, thistokens.copy(), doc, node.data, node.listidx)
                    else:
                        match = TokenGazetteerMatch(i, i + 1, thistokens.copy(), doc, node.data, node.listidx)
                    thismatches.append(match)
                j = i+1  # index into text tokens
                nignored = 0
                while j <= toidx:
                    logger.debug(f"j={j}")
                    if node.nodes:
                        tok_obj = tokens[j]
                        tok = self.getterfunc(tok_obj)
                        if self.mapfunc:
                            tok = self.mapfunc(tok)
                        if self.ignorefunc and self.ignorefunc(tok):
                            j += 1
                            nignored += 1
                            continue
                        if tok in node.nodes:
                            logger.debug(f"Found token {tok}")
                            node = node.nodes[tok]
                            thistokens.append(tok_obj)
                            if node.is_match:
                                logger.debug(f"Also is entry match")
                                if matchfunc:
                                    match = matchfunc(
                                        i, i + len(thistokens)+nignored,
                                        thistokens.copy(),
                                        doc,
                                        node.data, node.listidx)
                                else:
                                    match = TokenGazetteerMatch(
                                        i, i + len(thistokens)+nignored,
                                        thistokens.copy(),
                                        doc,
                                        node.data, node.listidx)
                                # TODO: should LONGEST get calculated including ignored tokens or not?
                                if all:
                                    thismatches.append(match)
                                    if len(thistokens) > longest:
                                        longest = len(thistokens)
                                else:
                                    if len(thistokens) > longest:
                                        thismatches = [match]
                                        longest = len(thistokens)
                            j += 1
                            continue
                        else:
                            logger.debug(f"Breaking: {tok} does not match, j={j}")
                            break
                    else:
                        logger.debug("Breaking: no nodes")
                        break
                logger.debug(f"Going through thismatches: {thismatches}")
                for m in thismatches:
                    matches.append(m)
                if thismatches and skip:
                    i += longest - 1  # we will increment by 1 right after!
            i += 1
            logger.debug(f"Incremented i to {i}")
        return matches

    def __call__(self, doc, annset=None, tokentype=None, septype=None, splittype=None, withintype=None):
        """
        Apply the gazetteer to the document and annotate all matches.

        Args:
            doc: the document to annotate with matches.
            annset: if given, overrides the one specified for the gazetteer instance.
            tokentype: if given, overrides the one specified for the gazetteer instance.
            septype: if given, overrides the one specified for the gazetteer instance.
            splittype: if given, overrides the one specified for the gazetteer instance.
            withintype: if given, overrides the one specified for the gazetteer instance.

        Returns:
            the annotated document
        """
        pass


####################### TODO

import sys


def thisorthat(x,y): x if x is not None else y


@dataclass(unsafe_hash=True, order=True)
class Match:
    __slots__ = ("start", "end", "match", "entrydata", "matcherdata")
    start: int
    end: int
    match: list
    entrydata: object
    matcherdata: object


_NOVALUE = object()


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
            print(f"Node(val=,children=[", end="", file=file)
        else:
            print(f"Node(val={self.value},children=[",end="", file=file)
        for c, n in self.children.items():
            print(f"{c}:", end="",file=file)
            n.print_node()
        print("])", end="", file=file)


class StringMatcher:

    def __init__(self, ignorefunc=None, mapfunc=None, matcherdata=None, defaultdata=None):
        """
        Create a TokenMatcher.
        :param ignorefunc: a predicate that returns True for any token that should be ignored.
        :param mapfunc: a function that returns the string to use for each token.
        :param matcherdata: data to add to all matches in the matcherdata field
        :param defaultdata: data to add to matches when the entry data is None
        """
        # TODO: need to figure out how to handle word boundaries
        # TODO: need to figure out how to handle matching spaces vs. different spaces / no spaces!
        # self.nodes = defaultdict(Node)
        self.ignorefunc = ignorefunc
        self.mapfunc = mapfunc
        self.defaultdata = defaultdata
        self.matcherdata = matcherdata
        self._root = _Node()

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

    def find(self, text, all=False, skip=True, fromidx=None, toidx=None, matchmaker=None):
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
        logger = ensurelogger()
        logger.debug("CALL")
        matches = []
        l = len(text)
        if fromidx is None:
            fromidx = 0
        if toidx is None:
            toidx = l-1
        if fromidx >= l:
            return matches
        if toidx >= l:
            toidx = l-1
        if fromidx > toidx:
            return matches
        i = fromidx
        logger.debug(f"From index {i} to index {toidx} for {text}")
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
                    cur_len = k+1
                    if matchmaker:
                        match = matchmaker(i, i + k + 1, text[i:i+k+1], thisorthat(node.value, self.defaultdata), self.matcherdata)
                    else:
                        match = Match(i, i + k + 1, text[i:i+k+1], thisorthat(node.value, self.defaultdata), self.matcherdata)
                    if all:
                        matches.append(match)
                    else:
                        # NOTE: only one longest match is possible, but it can have a list of data if append=True
                        if cur_len > longest_len:
                            longest_len = cur_len
                            longest_match = match
                while True:
                    k += 1
                    if i+k >= len(text):
                        break
                    chr = text[i+k]
                    if self.ignorefunc and self.ignorefunc(chr):
                        continue
                    if self.mapfunc:
                        chr = self.mapfunc(chr)
                    node = node.children.get(chr)
                    break
                if i+k >= len(text):
                    break
            if not all and longest_match is not None:
                matches.append(longest_match)
            if skip:
                i += max(k,1)
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

        :param key: the key for which to find a node
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

    def replace(self,  text, fromidx=None, toidx=None, getter=None, replacer=None, matchmaker=None):
        matches = self.find(text, fromidx=fromidx, toidx=toidx, all=False, skip=True, matchmaker=matchmaker)
        if len(matches) == 0:
            return text
        parts = []
        last = 0
        for match in matches:
            if match.start > last:
                parts.append(text[last:match.start])
            if match.start >= last:
                if replacer:
                    rep = replacer(match)
                else:
                    rep = str(match.entrydata)
                parts.append(rep)
                last = match.end
        if last < len(text):
            parts.append(text[last:])
        return "".join(parts)