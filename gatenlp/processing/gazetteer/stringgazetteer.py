"""
This module provides the StringGazetter for matching strings against the text in a document.
"""
import sys, os
from typing import Union, Any, Tuple, List, Dict, Set, Optional, Callable
# note: recordclass is in extra basic, so for this need to install at least gatenlp[basic]
from recordclass import structclass
from gatenlp.utils import init_logger
from gatenlp.processing.gazetteer.base import GazetteerAnnotator

_NOVALUE = None

# NOTE: sthis was a dataclass originally
StringGazetteerMatch = structclass(
    "StringGazetteerMatch", ("start", "end", "match", "data", "listidxs")
)

# TODO: maybe add parameter compress_ws to make compression on reading and one-to-many matching optional
#    also, need to implement compression/cleaning on read!
# TODO: add mapfun for one-to-one character mappings only: use when reading entries and when reading a char
#    from the text to do things like lowercase! Maybe provide predefined mapping callables like Lower, in the base.py
# TODO: make sure a ready/loaded gazetteer is pickleable as a whole so we can transfer to another process
# TODO: however also check what our idea was to defer initializing/loading through config parms?
# TODO: alternative approach: a pipeline can also have arbitrary steps/code to
#    1) complete one-time initialization (e.g. load gazetteer): this gets run when the pipeline has been created on
#    the other machine or process and 2) code to run before processing a source/corpus starts

class _Node:
    """
    Trie Node: represents the value and the children.
    """

    __slots__ = ("children", "value", "listidxs")

    def __init__(self) -> None:
        self.children: dict = dict()
        self.value: Optional[Union[Dict, List[Dict]]] = _NOVALUE
        self.listidxs: Optional[Union[int, List[int]]] = _NOVALUE

    def is_match(self) -> bool:
        """
        Returns:
            True if this node corresponds to a match.
        """
        return self.value != _NOVALUE

    def data(self) -> Tuple[List[Dict], List[int]]:
        """
        Returns:
            The data for this node
        """
        val = self.value
        if val is None:
            val = []
        elif not isinstance(val, list):
            val = [val]
        idxs = self.listidxs
        if idxs is None:
            idxs = []
        elif not isinstance(idxs, list):
            idxs = [idxs]
        return val, idxs

    def print_node(self, file=sys.stderr, recursive: bool = True) -> None:
        print(f"Node(value={self.value},listidxs={self.listidxs},children=[", end="", file=file)
        if recursive:
            for c, n in self.children.items():
                print(f"{c}:", end="", file=file)
                n.print_node()
        else:
            print(f"({len(self.children)} children)", file=file)
        print("])", end="", file=file)


class StringGazetteer(GazetteerAnnotator):
    def __init__(
            self,
            outset_name: str = "",
            ann_type: str = "Lookup",
            longest_only: bool = False,
            skip_longest: bool = False,
            start_type: Optional[str] = None,
            end_type: Optional[str] = None,
            ws_chars: Union[None, str, Callable] = None,
            ws_type: Optional[str] = None,
            split_chars: Union[None, str, Callable] = None,
            split_type: Optional[str] = None,
    ):
        """
        Create a String Gazetteer annotor.

        Args:
            outset_name: the name of the output annotation set where to place the annotations for matches
            ann_type: the annotation type name to use for match annotations, unless overriden by a load method
            longest_only: if True, only return the data for the longest match at each position, otherwise
                return the data for all matches
            skip_longest: if True, find the next match after the longest match at a position, otherwise try to
                find from next possible offset
            start_type: if not None, the annotation type of annotations defining possible starting points of matches,
                if None, matches can occur anywhere
            end_type: if not None, the annotation type of annotations defining possible end points of matches, if
                None, matches can end anywhere
            ws_chars: if None and whitespace checking is not based on offsets, use the python isspace() method.
                Otherwise should be a string containing the possible WS characters or a callable that returns
                True for WS
            ws_type: the annotation type of annotations indicating whitespace, if specified, ws_chars is ignored
            split_chars: if None and split character checking is not based on offsets, use a default list of new line
                and similar characters (see https://docs.python.org/3/library/stdtypes.html#str.splitlines).
                Otherwise should be a string containing the possible split characters or a callable that returns
                True for split characters
            split_type: the annotation type of annotations indicating splits, if specified, split_chars is ignored
        """
        self._root: _Node = _Node()
        self.outset_name = outset_name
        self.ann_type = ann_type
        self.logger = init_logger(__name__)
        self.longest_only: bool = longest_only
        self.skip_longest: bool = skip_longest
        self.start_type = start_type
        self.end_type = end_type
        self.ws_chars = ws_chars
        self.ws_type = ws_type
        self.split_chars = split_chars
        self.split_type = split_type
        if self.ws_chars is None:
            self.ws_chars_func = str.isspace
        elif isinstance(self.ws_chars, str):
            self.ws_chars_func = lambda x: x in self.ws_chars
        else:
            self.ws_chars_func = self.ws_chars
        if self.split_chars is None:
            self.split_chars_func = lambda x: x in "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"
        elif isinstance(self.split_chars, str):
            self.split_chars_func = lambda x: x in self.split_chars
        else:
            self.split_chars_func = self.split_chars
        self.list_features: List[Dict] = []
        self.list_types: List[str] = []

    def add(self, entry: Union[str, None], data: Union[None, dict] = None, listidx: Union[None, int] = None):
        """
        Add a gazetteer entry or several entries if "entry" is not a string but iterable and store its data.

        If data is not None, it is stored or added to a list of data stored with the entry. If listidx is not None
        it is stored or added to a list of listidxs stored with the entry. If data and listidx are None a match with
        empty data (and empty dict) is stored with the entry.
        If all elements of the entry are ignored, nothing is done.

        Important: this does not modify the entry itself in any way, whitespace trimming and normalization must be
            done before calling this method!

        Args:
            entry: a string or an iterable of strings
            data: the data to add for that gazetteer entry or None to add no data.
            listidx: the list index to add or None
        """
        if isinstance(entry, str):
            entry = [entry]
        for e in entry:
            if e is None or e == "" or not isinstance(e, str):
                raise Exception(f"Cannot add gazetteer entry '{e}' must be a non-empty string")
            node = self._get_node(e, create=True)
            if node == self._root:
                # empty string not allowed
                raise Exception(f"Cannot add gazetteer entry '{e}', matches root node")
            if node.value == _NOVALUE:
                if data is None:
                    node.value = {}
                else:
                    node.value = data
            else:
                if data is not None:
                    if isinstance(node.value, list):
                        node.value.append(data)
                    else:
                        node.value = [node.value]
                        node.value.append(data)
            if node.listidxs == _NOVALUE:
                if listidx is not None:
                    node.listidxs = listidx
            else:
                if listidx is not None:
                    if isinstance(node.listidxs, list):
                        node.listidxs.append(listidx)
                    else:
                        node.listidxs = [node.listidxs]
                        node.listidxs.append(listidx)

    def append(self,
               source: Any = None,
               fmt: str = "gate-def",
               source_encoding: str = "utf-8",
               source_sep: str = "\t",
               list_features: Optional[Dict] = None,
               list_type: Optional[str] = None,
               list_nr: Optional[int] = None
               ):
        """
        Append gazetteer entries from the given source to the gazetteer. Depending on the format this can load
        one or more gazetteer lists, where each list can share common list-spcific features and can have an optional
        list-specific annotation type to use.

        Args:
            source: the source to use, e.g. a file
            fmt: the format of the source, one of "gate-def": a GATE def file, "gazlist": a list of tuples with 2
                elements, where the first element is the gazetteer entry (string), and the second is a dictionary of
                features
            source_encoding: the encoding of any source gazetteer files
            source_sep: the field separator used in source gazetteer files
            list_features: the features to use for the list or lists that get loaded from the source,
                if None, no features are used/added to the list.
            list_type: the annotation type to use for the list/lists loaded, if None, the type
                specified with the constructor is used.
            list_nr: only for fmt "gazlist", if not None, the number of an already existing/loaded list,
                otherwise the next list number is used. If an existing list number is used, any features are added,
                the type is overriden and all entries are added to that list.
        """
        if fmt == "gazlist":
            if list_nr is not None:
                assert int(list_nr) == list_nr and 0 < list_nr < len(self.list_features)
                if list_features is not None:
                    self.list_features[list_nr].update(list_features)
                if list_type is not None:
                    self.list_types[list_nr] = list_type
            else:
                list_nr = len(self.list_features)
                if list_features is not None:
                    self.list_features.append(list_features)
                else:
                    self.list_features.append({})
                if list_type is not None:
                    self.list_types.append(list_type)
                else:
                    self.list_types.append(self.ann_type)
            for el in source:
                entry = el[0]
                data = el[1]
                self.add(entry, data, listidx=list_nr)
        elif fmt == "gate-def":
            if list_features is None:
                listfeatures = {}
            if list_type is None:
                listtype = self.ann_type
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
                    self.logger.info(f"Reading list file {listfile}")
                    with open(listfile, "rt", encoding=source_encoding) as inlistfile:
                        self.list_types.append(this_outtype)
                        self.list_features.append(this_listfeatures)
                        linenr = 0
                        for listline in inlistfile:
                            linenr += 1
                            listline = listline.rstrip("\n\r")
                            fields = listline.split(source_sep)
                            entry = fields[0]
                            # TODO: make sure we normalize, prepare the entry and check it is not empty!
                            # should trim and compress ws
                            if len(entry) > 1:
                                feats = {}
                                for fspec in fields[1:]:
                                    fname, fval = fspec.split("=")
                                    feats[fname] = fval
                            else:
                                feats = None
                            listidx = len(self.list_features) - 1
                            self.add(entry, feats, listidx=listidx)
        else:
            raise Exception(f"TokenGazetteer format {fmt} not known")

    def is_ws(self, char, off, ws_offsets):
        """
        Return True if the character or offset is corresponding to a whitespace character.
        If ws_offsets is None, then this is true if chr.isspace() is true, otherwise if the off is in ws_offsets.

        Args:
            char: the character to check
            off: the offset to check
            ws_offsets: the known whitespace offsets or None if we should check the character instead of the offset

        Returns:
            True if we have a whitespace character
        """
        if ws_offsets is not None:
            return off in ws_offsets
        else:
            return self.ws_chars_func(char)

    def is_split(self, char, off, split_offsets):
        if split_offsets is not None:
            return off in split_offsets
        else:
            return self.split_chars_func(char)

    def match(self, text: str, start: int = 0, end: Union[None, int] = None, longest_only: Union[None, bool] = None,
              start_offsets: Union[List, Set, None] = None,
              end_offsets: Union[List, Set, None] = None,
              ws_offsets: Union[List, Set, None] = None,
              split_offsets: Union[List, Set, None] = None,
              ):
        """
        Try to start at offset start in text, if end is not None, do not match beyond end offset.

        Args:
            text: the text/string in which to find matches
            start: the offset where the match must start
            end: if not None, the offset beyond which a match is not allowed to end
            longest_only:  if True, return only the longest matches, otherwise return all matches. If None, uses the setting
                from init.
            start_offsets: if not None, should be a list or set of possible start offsets. This function will only
                find a match if the given start offset is valid
            end_offsets: if not None, should be a list of set of possible end offsets. Only matches ending at a valid
                offset are considered
            ws_offsets: if not None, should be a list/set of offsets which contain whitespace. Any offset considered
                whitespace will get mapped to an actual space character for matching the gazetteer entry
            split_offsets: if not None, should be a list or set of offsets which are considered splits, i.e. something
                across no matching is possible
        Returns:
            A tuple where the first element is a list of StringGazetteerMatch objects and the second the length
            of the longest match, 0 if there is no match (list of match objects is empty).
        """
        # NOTE: this method does not check for any start condition (e.g. word start), the caller should do this!

        if longest_only is None:
            longest_only = self.longest_only
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
        if start_offsets is not None and start not in start_offsets:
            return matches, 0
        cur_chr = text[start]
        longest_len = 0
        longest_match = None
        node = self._root
        # if the current character is whitespace, map it to the character we use to represent whitespace in the
        # the gazetteer
        if self.is_ws(cur_chr, start, ws_offsets):
            cur_chr = " "
        node = node.children.get(cur_chr)
        cur_off = start
        while node is not None:
            if node.is_match():
                cur_end = cur_off + 1
                # we found a match, but if we have end offsets, also check if the end offset is valid
                if end_offsets is None or (end_offsets is not None and cur_end in end_offsets):
                    cur_len = cur_end - start
                    vals, idxs = node.data()
                    match = StringGazetteerMatch(
                        start,
                        cur_end,
                        text[start: cur_end],
                        vals,
                        idxs,
                    )
                    if not longest_only:
                        matches.append(match)
                    else:
                        if cur_len > longest_len:
                            longest_len = cur_len
                            longest_match = match
            # if the current node/character corresponds to a whitespace character and compress whitespace is True,
            # then match any additional whitespace characters in the text
            # BUT: only if compress_ws is True
            # BUT: only until we have reached the end of the match area or until we have reached a split character
            have_ws = self.is_ws(cur_chr, cur_off, ws_offsets)
            do_break = False
            while True:
                cur_off += 1
                cur_chr = text[cur_off]
                # ok we have reached the end
                if cur_off >= end:
                    do_break = True
                    break
                # we have reached a split
                if self.is_split(cur_chr, cur_off, split_offsets):
                    do_break = True
                    break
                # if we did not have a WS char, definitely already break after one time through the above code
                if not have_ws:
                    break
                # otherwise we go through this loop again, until we reach some other exit condition (end, split)
                # tested above or we hit a character that is not a whitespace:
                if not self.is_ws(cur_chr, cur_off, ws_offsets):
                    break
            # if we found end/split, end all
            if do_break:
                break
            # before we continue, get node for the character we have now
            node = node.children.get(chr)
        if longest_only and longest_match is not None:
            matches.append(longest_match)
        return matches, longest_len

    def find(self,
             text: str, start: int = 0, end: Union[None, int] = None,
             longest_only: Union[None, bool] = None,
             start_offsets: Union[List, Set, None] = None,
             end_offsets: Union[List, Set, None] = None,
             ws_offsets: Union[List, Set, None] = None,
             split_offsets: Union[List, Set, None] = None,
    ):
        """
        Find the next gazetteer match(es) in the text, if any.

        Args:
            text: string to search
            start: offset where to start matching in the text
            end: if not None, offset beyond which no match may happen (start or end)
            longest_only: if True, return only the longest match at each position
            start_offsets: if not None, a list/set of offsets where a match can start
            end_offsets: if not None, a list/set of offsets where a match can end
            ws_offsets: if not None, a list/set of offsets which are considered whitespace
            split_offsets: if not None, a list/set of offsets which are considered split locations

        Returns:
            A triple with the list of matches as the first element, the max length of matches or 0 if no matches
            as the second element and the index where the match occurs or None as the third element
        """
        if longest_only is None:
            longest_only = self.longest_only
        offset = start
        if end is None:
            end = len(text) - 1
        while offset <= end:
            if self.is_ws(text[offset], offset, ws_offsets):
                continue
            if self.is_split(text[offset], offset, ws_offsets):
                continue
            if start_offsets is not None and offset not in start_offsets:
                continue
            matches, long = self.match(text, start=offset, end=end, longest_only=longest_only,
                                       start_offsets=start_offsets, end_offsets=end_offsets,
                                       ws_offsets=ws_offsets, split_offsets=split_offsets
                                       )
            if long == 0:
                offset += 1
                continue
            return matches, long, offset
        return [], 0, None

    def find_all(self,
                 text: str, start: int = 0, end: Union[None, int] = None,
                 longest_only: Union[None, bool] = None,
                 skip_longest: Union[None, bool] = None,
                 start_offsets: Union[List, Set, None] = None,
                 end_offsets: Union[List, Set, None] = None,
                 ws_offsets: Union[List, Set, None] = None,
                 split_offsets: Union[List, Set, None] = None,):
        """
        Find the next gazetteer match(es) in the text, if any.

        Args:
            text: string to search
            start: offset where to start matching in the text
            end: if not None, offset beyond which no match may happen (start or end)
            longest_only: if True, return only the longest match at each position, if None use gazetteer setting
            skip_longest: if True, find next match after longest match, if None use gazetteer setting
            start_offsets: if not None, a list/set of offsets where a match can start
            end_offsets: if not None, a list/set of offsets where a match can end
            ws_offsets: if not None, a list/set of offsets which are considered whitespace
            split_offsets: if not None, a list/set of offsets which are considered split locations

        Yields:
            list of matches
        """
        if skip_longest is None:
            skip_longest = self.skip_longest
        if longest_only is None:
            longest_only = self.longest_only
        offset = start
        if end is None:
            end = len(text) - 1
        while offset <= end:
            if self.is_ws(text[offset], offset, ws_offsets):
                continue
            if self.is_split(text[offset], offset, ws_offsets):
                continue
            if start_offsets is not None and offset not in start_offsets:
                continue
            matches, maxlen, where = self.find(text, start=offset, end=end, longest_only=longest_only,
                                               start_offsets=start_offsets, end_offsets=end_offsets,
                                               ws_offsets=ws_offsets, split_offsets=split_offsets
                                               )
            if where is None:
                return
            yield matches
            if skip_longest:
                offset += maxlen
            else:
                offset += 1
        return

    def __setitem__(self, key, valuesandidxs: Tuple[Union[List[Dict], Dict], Union[List[int], int]]):
        assert isinstance(valuesandidxs, tuple)
        assert len(valuesandidxs) == 2
        assert isinstance(valuesandidxs[0], (dict, list))
        assert isinstance(valuesandidxs[1], (int, list))
        node = self._get_node(key, create=True)
        node.value, node.listidxs = valuesandidxs

    def __getitem__(self, item):
        """
        Return the data corresponding the to given item or raise a KeyError exception if not found.
        The data is a tuple where the first element is
        a list of dicts and the second element is a list of list indices.

        Args:
            item: the string to look up

        Returns:
            A tuple (listofdicts, listofindices)

        Raises:
            KeyError if the item is not found
        """
        node = self._get_node(item, create=False, raise_error=True)
        if not node.is_match():
            raise KeyError(item)
        return node.data()

    def get(self, item: str, default: Tuple[Any, Any] = (None, None)) -> Tuple[Union[None, List[Dict]], Union[None, List[int]]]:
        """
        Return the data corresponding the to given item. The data is a tuple where the first element is
        a list of dicts and the second element is a list of list indices. If the item is not found, the given default
        is returned instead

        Args:
            item: the string to look up
            default: the return value if not found

        Returns:
            A tuple (listofdicts, listofindices) or (None, None) / the default value if not found
        """
        node = self._get_node(item, create=False, raise_error=False)
        if not node.is_match():
            return default
        return node.data()

    def _get_node(self, item: str, create: bool = False, raise_error: bool = True) -> Union[None, _Node]:
        """
        Returns the node corresponding to the item, if not found either create or return None or raise a KeyError.

        Args:
            item: the string for which to find a node
            create: if True, insert all necessary nodes
            raise_error: if True and create is False, raises an error if not found, if False, returns None
        Returns:
            the node corresponding to the key or None if no node found and raise_error is False
        """
        node = self._root
        for el in item:
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
