"""
This module provides Gazetteer classes which allow matching the text or the tokens of documents against
gazetteer lists, lists of interesting texts or token sequences and annotate the matches with features from the
gazetteer lists.
"""

import os
from typing import Union, Dict, Optional, Callable, List
from collections import defaultdict
from recordclass import structclass

from gatenlp.document import Document, Annotation
from gatenlp.utils import init_logger
from gatenlp.processing.annotator import Annotator
from gatenlp.processing.gazetteer.base import GazetteerBase

# TODO: better handling/support for separator annotations: this would add complexity but allow that a sequence
#   of annotations is only matched if there is a/several? separator annotation between each of those annotations.
#   Could also require this only if there is a separator in the gazetteer sequence (e.g. indicated by a None element)


# NOTE! this was origiannl a @dataclass(unsafe_hash=True, order=True)
# class TokenGazetteerMatch, with __slots__=("start", "end", "match", "entrydata", "matcherdata")
# and type declarations start: int, end: int, match: list, entrydata: object, matcherdata: object
# HOWEVER, dataclasses require Python 3.7 and have their own issues.
# Named tuples cannot be used because what we need has to be mutable.
# So for now we use the structclass approach from package recordclass which is very compact and rather fast.
# !! structclass by default does NOT support cyclic garbage collection which should be ok for us


TokenGazetteerMatch = structclass(
    "TokenGazetteerMatch", ("start", "end", "match", "data", "listidx")
)


class TokenGazetteerNode:
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
        return f"Node(is_match={self.is_match},data={self.data},listidx={self.listidx},nodes={nodes})"


def tokentext_getter(token, doc=None, feature=None):
    if feature is not None:
        txt = token.features.get(feature)
    else:
        if doc is None:
            raise Exception("No feature given, need doc for gazetteer")
        txt = doc[token]
    return txt


# TODO: allow output annotation type to be set from the match or from the list!
class TokenGazetteer(GazetteerBase):
    def __init__(
        self,
        source: Union[List, str, None] = None,
        source_fmt: str = "gate-def",
        source_sep="\t",
        source_encoding="UTF-8",
        # cache_source=None,   # TODO
        source_tokenizer: Union[None, Annotator, Callable] = None,
        longest_only: bool = False,
        skip_longest: bool = False,
        outset_name: str = "",
        ann_type: str = "Lookup",
        annset_name: str = "",
        token_type: str = "Token",
        feature=None,
        split_type: Optional[str] = None,
        within_type: Optional[str] = None,
        mapfunc: Optional[Callable] = None,
        ignorefunc: Optional[Callable] = None,
        getterfunc: Optional[Callable] = None,
        list_features: Optional[Dict] = None,
        list_type: Optional[str] = None,
    ):
        """

        Args:
            source: where to load the gazetteer from. What is actually expected here depends on the fmt
              parameter. If none, nothing is loaded
            source_fmt: defines what is expected as the format and/or content of the source parameter. One of:
               *  "gate-def" (default): the path to a GATE-style "def" file.
                  See https://gate.ac.uk/userguide/chap:gazetteers
               * "gazlist": a list of tuples or lists where the first element of the tuple/list
                  is a list of strings and the second element is a dictionary containing the features to assign.
                  All entries in the list belong to the first gazetteer list which has list features as
                  specified with the listfeatures parameter and a list type as specified with the listtype parameter.
            source_sep: the field separator to use for some source formats (default: tab character)
            source_encoding: the encoding to use for some source formats (default: UTF-8)
            source_tokenizer: if not None, an annotator, that creates annotations of type "Token" in the default
                annotation set. If this is None, then when loading string gazetteer entries, they are tokenized by
                splitting on whitespace (as defined by Python str.split())
            feature: the feature name to use to get the string for each token. If the corresponding feature
                in the token does not exist, is None or is the empty string, the Token is completely ignored.
                If the feature parameter is None, use the document string covered by the token.
            longest_only: if True, only returns the longest match at each matching position, otherwise returns all
                matches.
            skip_longest: skip forward over longest match (do not return contained/overlapping matches)
            annset_name: the set where the tokens to match should come from
            outset_name: the set where the new annotations are added
            ann_type: the annotation type of the annotations to create, unless a type is given for the gazetteer
                entry or for the gazetteer list.
            token_type: the annotation type of the token annotations
            split_type: the annotation type of any split annotations which will end any ongoing match
            within_type: only matches fully within annotations of this type will be made
            mapfunc: a callable that maps the original string extracted for each token to the actual string to use.
            ignorefunc: a callable which given the mapped token string decides if the token should be ignored
                (not added to the gazetteer list, not considered in the document when matching)
            getterfunc: a callable which, given a token annotation, retrieves the string. If there is mapfunc, the
                retrieved string is then still run through the mapfunc. The getterfunc must accept the token and
                an optional document as parameters.
            list_features: a dictionary of features common to the whole list loaded or None.
                If what gets loaded specifies
                its own list features, this is getting ignored.
            list_type: the output annotation type to use for the list, ignored if the input format specifies this
                on its own. If the input does not specify this on its own and this is not None, then it takes
                precedence over outtype for the data loaded from source.

        """
        self.nodes = defaultdict(TokenGazetteerNode)
        self.mapfunc = mapfunc
        self.ignorefunc = ignorefunc
        self.feature = feature
        self.annset = annset_name
        self.tokentype = token_type
        self.splittype = split_type
        self.withintype = within_type
        self.outset = outset_name
        self.outtype = ann_type
        self.longest_only = longest_only
        self.skip = skip_longest
        if getterfunc:
            self.getterfunc = getterfunc
        else:
            self.getterfunc = tokentext_getter
        self.listfeatures = []
        self.listtypes = []
        self.logger = init_logger(__name__)
        # self.logger.setLevel(logging.DEBUG)
        self.size = 0
        if source is not None:
            self.append(source, source_fmt=source_fmt,
                        list_features=list_features, list_type=list_type, source_sep=source_sep,
                        source_encoding=source_encoding, source_tokenizer=source_tokenizer
                        )

    def append(
        self,
        source:  Union[None, str, List],
        source_fmt: str = "gate-def",
        source_sep: str = "\t",
        source_encoding: str = "UTF-8",
        source_tokenizer: Union[None, Annotator, Callable] = None,
        source_splitter: Optional[Callable] = None,
        list_features: Optional[Dict] = None,
        list_type: Optional[str] = None,
    ):
        """
        This method appends more entries to gazetteer.

        Args:
            source: where to load the gazetteer from. What is actually expected here depends on the fmt
              parameter.
            source_fmt: defines what is expected as the format and/or content of the source parameter. One of:
               *  "gate-def" (default): source must be a string, a pathlib Path or a parsed urllib url and
                  point to a GATE-style "def" file. See https://gate.ac.uk/userguide/chap:gazetteers
               * "gazlist": a list of tuples or lists where the first element of the tuple/list
                  is a list of strings, the second element is a dictionary containing the features to assign and
                  the third element, if it exists, is the index of an element in the listfeatures array.
            source_sep: the field separator to use for some source formats (default: tab character)
            source_encoding: the encoding to use for some source formats (default: UTF-8)
            source_tokenizer: if not None, an annotator, that creates annotations of type "Token" in the default
                annotation set. If this is None, then when loading string gazetteer entries, they are tokenized by
                splitting on whitespace (as defined by Python str.split())
            source_splitter: if not None and source_tokenizer is None, a callable that takes a string and returns
                the tokenstrings to use
            list_features: a list of dictionaries containing the features to set for all matches witch have the
              list index set, this list gets appended to the existing listfeatures. If what gets appended specifies
              its own list features, this is ignored.
            list_type: the output annotation type to use for the list that gets appended. If what gets appended
               specifies its own list type or list types, this is ignored.
        """
        if source_fmt == "gazlist":
            if list_features is not None:
                self.listfeatures.append(list_features)
            else:
                self.listfeatures.append({})
            if list_type is not None:
                self.listtypes.append(list_type)
            else:
                self.listtypes.append(self.outtype)
            listidx = len(self.listfeatures) - 1
            for el in source:
                entry = el[0]
                data = el[1]
                self.add(entry, data, listidx=listidx)
        elif source_fmt == "gate-def":
            if list_features is None:
                list_features = {}
            if list_type is None:
                list_type = self.outtype
            with open(source, "rt", encoding=source_encoding) as infp:
                for line in infp:
                    line = line.rstrip("\n\r")
                    fields = line.split(":")
                    fields.extend(["", "", "", ""])
                    listFile = fields[0]
                    majorType = fields[1]
                    minorType = fields[2]
                    languages = fields[3]
                    anntype = fields[4]
                    this_listfeatures = list_features.copy()
                    this_outtype = list_type
                    if majorType:
                        this_listfeatures["majorType"] = majorType
                    if minorType:
                        this_listfeatures["minorType"] = minorType
                    if languages:
                        this_listfeatures["lang"] = languages
                    if anntype:
                        this_outtype = anntype
                    # read in the actual list
                    listfile = os.path.join(os.path.dirname(source), listFile)
                    self.logger.debug(f"Reading list file {listfile}")
                    with open(listfile, "rt", encoding=source_encoding) as inlistfile:
                        self.listtypes.append(this_outtype)
                        self.listfeatures.append(this_listfeatures)
                        linenr = 0
                        for listline in inlistfile:
                            linenr += 1
                            listline = listline.rstrip("\n\r")
                            fields = listline.split(source_sep)
                            entry = fields[0]
                            if source_tokenizer or source_splitter:
                                if source_tokenizer:
                                    tmpdoc = Document(entry)
                                    tmpdoc = source_tokenizer(tmpdoc)  # we MUST reassign here to allow return of a new doc!
                                    tokenanns = list(tmpdoc.annset().with_type("Token"))
                                    if self.getterfunc:
                                        tokenstrings = [
                                            self.getterfunc(a, doc=tmpdoc)
                                            for a in tokenanns
                                        ]
                                    else:
                                        tokenstrings = [tmpdoc[a] for a in tokenanns]
                                else:
                                    tokenstrings = source_splitter(entry)
                                if self.mapfunc:
                                    tokenstrings = [
                                        self.mapfunc(s) for s in tokenstrings
                                    ]
                                if self.ignorefunc:
                                    tokenstrings = [
                                        s
                                        for s in tokenstrings
                                        if not self.ignorefunc(s)
                                    ]
                            else:
                                tokenstrings = entry.split()  # just split on whitespace
                            if len(tokenstrings) == 0:
                                self.logger.warning(
                                    f"File {listfile}, skipping line {linenr}, no tokens left: {listline}"
                                )
                                continue
                            if len(entry) > 1:
                                feats = {}
                                for fspec in fields[1:]:
                                    fname, fval = fspec.split("=")
                                    feats[fname] = fval
                            else:
                                feats = None
                            listidx = len(self.listfeatures) - 1
                            self.add(tokenstrings, feats, listidx=listidx)
        else:
            raise Exception(f"TokenGazetteer format {source_fmt} not known")

    def add(self, entry, data=None, listidx=None):
        """
        Add a single gazetteer entry. A gazetteer entry can have no data associated with it at all if both
        data and listidx are None. If only list indices are given then an array of those indices is stored
        with the entry and data remaines None, if only data is given then an array of data is stored and
        listidx remains None. If at some point, both data and a listidx are stored in the same entry, then
        both fields are changed to have both a list with the same number of elements corresponding to each
        other, with missing data or listidx elements being None.

        Args:
            entry: a iterable of string or a string for a single element, each element is the string that
               represents a token to be matched
            data: dictionary of features to add
            listidx: the index to list features and a list type to add
        """
        if isinstance(entry, str):
            entry = [entry]
        node = None
        i = 0
        for token in entry:
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
        self.size += 1
        # For now: always store parallel lists of data and listidxs, with None elements if necessary.
        if data is not None or listidx is not None:
            if node.data is None:
                node.data = [data]
                node.listidx = [listidx]
            else:
                node.data.append(data)
                node.listidx.append(listidx)

        # TODO: code to test and correct: try to save space by only storing parallel lists if
        # both data and listindices are actually both non-null and added:
        #
        # if data is None and listidx is None:
        #     # nothing to do, return what we have
        #     return node.data, node.listidx
        # # if we have only data and no listidx and there is no listidx
        # if data is not None and listidx is None and node.listidx is None:
        #     if node.data is None:
        #         node.data = [data]
        #     else:
        #         node.data.append(data)
        # elif listidx is not None and data is None and node.data is None:
        #     if node.listidx is None:
        #         node.listidx = [listidx]
        #     else:
        #         node.listidx.append(listidx)
        # else:
        #     # make sure we have parallel lists
        #     if node.data is None:
        #         node.data = []
        #     if node.listidx is None:
        #         node.listidx = []
        #     if len(node.data) > len(node.listidx):
        #         node.listidx.extend([None] * (len(node.data) - len(node.listidx)))
        #     elif len(node.listidx) > len(node.data):
        #         node.data.extend([None] * (len(node.listidx) - len(node.data)))
        #     if listidx:
        #         node.listidx.append(listidx)
        #         if data:
        #             node.data.append(data)
        #         else:
        #             node.data.append(None)
        #     else:
        #         node.listidx.append(None)
        #         node.listidx.append(listidx)

    def match(self, tokens, doc=None, longest_only=None, idx=0, endidx=None, matchfunc=None):
        """
        Try to match at index location idx of the tokens sequence. Returns a list which contains
        no elements if no match is found,  or
        as many elements as matches are found. The element for each match is either a
        TokenGazeteerMatch instance if matchfunc is None or whatever matchfunc returns for a match.
        Also returns the legngth of the longest match (0 if no match).

        Args:
            tokens: a list of tokens (must allow to fetch the ith token as tokens[i])
            doc: the document to which the tokens belong. Necessary of the underlying text is used
               for the tokens.
            longest_only: whether to return all matches or just the longest ones. If None, overrides the setting
               from init.
            idx: the index in tokens where the match must start
            endidx: the index in tokens after which no match must end
            matchfunc: a function to process each match.
               The function is passed the TokenGazetteerMatch and the doc and should return something
               that is then added to the result list of matches.

        Returns:
            A tuple, where the first element is a list of match elements, empty if no matches are found
            and the second element is the length of the longest match, 0 if no match.

        """
        if endidx is None:
            endidx = len(tokens)
        assert idx < endidx
        if longest_only is None:
            longest_only = self.longest_only
        token = tokens[idx]
        if token.type == self.splittype:
            return [], 0
        token_string = self.getterfunc(token, doc=doc, feature=self.feature)
        if token_string is None:
            return [], 0
        if self.mapfunc:
            token_string = self.mapfunc(token_string)
        if self.ignorefunc:
            if self.ignorefunc(token_string):
                # no match possible here
                return [], 0
        # check if we can match the current token
        if token_string in self.nodes:
            # ok, we have the beginning of a possible match
            longest = 0
            node = self.nodes[token_string]
            thismatches = []
            thistokens = [token]
            if node.is_match:
                # the first token is already a complete match, so we need to add this to thismatches
                longest = 1
                # TODO: make this work with list data!
                if matchfunc:
                    match = matchfunc(
                        idx, idx + 1, thistokens.copy(), node.data, node.listidx
                    )
                else:
                    match = TokenGazetteerMatch(
                        idx, idx + 1, thistokens.copy(), node.data, node.listidx
                    )
                thismatches.append(match)
            j = idx + 1  # index into text tokens
            nignored = 0
            while j < endidx:
                # print(f"!!! processing idx={j}/{endidx}")
                if node.nodes:
                    token = tokens[j]
                    if token.type == self.splittype:
                        break
                    token_string = self.getterfunc(token, doc=doc, feature=self.feature)
                    if token_string is None:
                        j += 1
                        nignored += 1
                        continue
                    if self.mapfunc:
                        token_string = self.mapfunc(token_string)
                    if self.ignorefunc and self.ignorefunc(token_string):
                        j += 1
                        nignored += 1
                        continue
                    if token_string in node.nodes:
                        node = node.nodes[token_string]
                        thistokens.append(token)
                        if node.is_match:
                            if matchfunc:
                                match = matchfunc(
                                    idx,
                                    idx + len(thistokens) + nignored,
                                    thistokens.copy(),
                                    node.data,
                                    node.listidx,
                                )
                            else:
                                match = TokenGazetteerMatch(
                                    idx,
                                    idx + len(thistokens) + nignored,
                                    thistokens.copy(),
                                    node.data,
                                    node.listidx,
                                )
                            # debugtxt = " ".join(
                            #     [doc[tokens[i]] for i in range(match.start, match.end)]
                            # )
                            # TODO: should LONGEST get calculated including ignored tokens or not?
                            if not longest_only:
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
                        break
                else:
                    break
            return thismatches, longest
        else:
            # first token did not match, nothing to be found
            return [], 0

    def find(
        self,
        tokens: List[Annotation],
        doc: Optional[Document] = None,
        longest_only: Optional[bool] = None,
        fromidx: Optional[int] = None,
        toidx: Optional[int] = None,
        endidx: Optional[int] = None,
        matchfunc: Optional[Callable] = None,
    ):
        """
        Find the next match in the given index range and return a tuple with two elements: the first element
        if the list of matches, empty if no match was found, the second element is the index where the matches
        were found or None if no match was found.

        Args:
            tokens: list of tokens (must allow to fetch the ith token as tokens[i])
            doc: the document to which the tokens belong. Necessary of the underlying text is used
               for the tokens.
            longest_only: whether to return all matches or just the longest ones. If not none, overrides the
               setting from init
            fromidx: first index where a match may start
            toidx: last index where a match may start
            endidx: the index in tokens after which no match must end
            matchfunc: the function to use to process each match

        Returns:
            A triple with the list of matches as the first element, the max length of matches or 0 if no matches
            as the second element and the index where the match occurs or None as the third element

        """
        if longest_only is None:
            longest_only = self.longest_only
        idx = fromidx
        if idx is None:
            idx = 0
        if toidx is None:
            toidx = len(tokens) - 1
        if endidx is None:
            endidx = len(tokens)
        while idx <= toidx:
            matches, long = self.match(
                tokens, idx=idx, doc=doc, longest_only=longest_only, endidx=endidx, matchfunc=matchfunc
            )
            if long == 0:
                idx += 1
                continue
            return matches, long, idx
        return [], 0, None

    def find_all(
        self,
        tokens: List[Annotation],
        doc: Optional[Document] = None,
        longest_only: Optional[bool] = None,
        skip_longest: Optional[bool] = None,
        fromidx: Optional[int] = None,
        toidx: Optional[int] = None,
        endidx: Optional[int] = None,
        matchfunc: Optional[Callable] = None,
        # reverse=True,
    ):
        """
        Find gazetteer entries in a sequence of tokens.
        Note: if fromidx or toidx are bigger than the length of the tokens allows, this is silently
        ignored.

        Args:
            tokens: iterable of tokens. The getter will be applied to each one and the doc to retrieve the initial
               string.
            doc: the document this should run on. Only necessary if the text to match is not retrieved from
               the token annotation, but from the underlying document text.
            longest_only: whether to return only the longest or all matches. If not None, overrides the init
               setting
            skip_longest: skip forward over longest match (do not return contained/overlapping matches). If not
               None overrides the init setting.
            fromidx: index where to start finding in tokens
            toidx: index where to stop finding in tokens (this is the last index actually used)
            endidx: index beyond which no matches should end
            matchfunc: a function which takes the data from the gazetteer, the token and doc and performs
                some action.

        Yields:
            list of matches
        """
        if longest_only is None:
            longest_only = self.longest_only
        if skip_longest is None:
            skip_longest = self.skip
        matches = []
        lentok = len(tokens)
        if endidx is None:
            endidx = lentok
        if fromidx is None:
            fromidx = 0
        if toidx is None:
            toidx = lentok - 1
        if fromidx >= lentok:
            yield matches
            return
        if toidx >= lentok:
            toidx = lentok - 1
        if fromidx > toidx:
            yield matches
            return
        idx = fromidx
        while idx <= toidx:
            matches, maxlen, idx = self.find(
                tokens,
                doc=doc,
                longest_only=longest_only,
                fromidx=idx,
                endidx=endidx,
                toidx=toidx,
                matchfunc=matchfunc,
            )
            if idx is None:
                return
            yield matches
            if skip_longest:
                idx += maxlen
            else:
                idx += 1

    def __call__(self, doc: Document, **kwargs) -> Document:
        """
        Apply the gazetteer to the document and annotate all matches.

        Args:
            doc: the document to annotate with matches.

        Returns:
            the annotated document
        """
        # create the token lists from the document: if withintype is None we only have one token list,
        # otherwise we have one list for each withingtype
        # We create a list of segments which are identified by start and end offsets
        if self.withintype is None:
            segment_offs = [(0, len(doc.text))]
        else:
            withinanns = doc.annset(self.withintype)
            segment_offs = []
            for wann in withinanns:
                segment_offs.append((wann.start, wann.end))
        anntypes = [self.tokentype]
        if self.splittype is not None:
            anntypes.append(self.splittype)
        anns = doc.annset(self.annset).with_type(anntypes)
        # now do the annotation process for each segment
        outset = doc.annset(self.outset)
        for segment_start, segment_end in segment_offs:
            tokens = list(anns.within(segment_start, segment_end))
            for matches in self.find_all(tokens, doc=doc):
                for match in matches:
                    starttoken = tokens[match.start]
                    endtoken = tokens[
                        match.end - 1
                    ]  # end is the index after the last match!!
                    startoffset = starttoken.start
                    endoffset = endtoken.end
                    if match.data:  # TODO: for now data and listidx are either both None or lists with same len
                        for data, listidx in zip(match.data, match.listidx):
                            outtype = self.outtype
                            feats = {}
                            if listidx is not None:
                                feats.update(self.listfeatures[listidx])
                                outtype = self.listtypes[listidx]
                            if "_gatenlp.gazetteer.outtype" in feats:
                                outtype = feats["_gatenlp.gazetteer.outtype"]
                                del feats["_gatenlp.gazetteer.outtype"]
                            if data is not None:
                                feats.update(data)
                            outset.add(startoffset, endoffset, outtype, features=feats)
                    else:
                        outset.add(startoffset, endoffset, self.outtype)
        return doc

    def get(self, tokenstrings, default=None):
        if isinstance(tokenstrings, str):
            tokenstrings = [tokenstrings]
        node = self.nodes
        for idx, tokenstring in enumerate(tokenstrings):
            if idx == 0:
                node = node.get(tokenstring)   # get from defaultdict
            else:
                node = node.nodes.get(tokenstring)   # get from TokenGazetteerNode nodes
            if node is None:
                return None
        if node.is_match:
            ret = []
            assert len(node.data) == len(node.listidx)
            for d, i in zip(node.data, node.listidx):
                new = d.copy()
                new.update(self.listfeatures[i])
                ret.append(new)
            return ret
        else:
            return default

    def __getitem__(self, tokenstrings):
        ret = self.get(tokenstrings)
        if ret is None:
            raise KeyError(tokenstrings)
        return ret

    def __contains__(self, tokenstrings):
        ret = self.get(tokenstrings)
        return ret is not None

    def __len__(self):
        return self.size
