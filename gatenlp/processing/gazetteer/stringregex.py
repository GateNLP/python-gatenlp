"""
Module that defines classes for matching annotators other than gazetteers which match e.g. regular expressions
of strings or annotations.
"""
import re
from typing import Union, List, Set, Optional, Dict, Iterable, Any, Tuple
from collections import namedtuple
from gatenlp import Document
from gatenlp.processing.gazetteer.stringgazetteer import StringGazetteer
from gatenlp.processing.gazetteer.base import GazetteerBase, Match

# rule body line:
# one or more comma separated group numbers followed by a "=>" followed by feature assignments
# each feature assignment is basically whatever can be inside a python "dict(...)" constructor.
# e.g. 0,3 => Lookup f1=2, f2 = "something" , f3=True

PAT_RULE_BODY_LINE = re.compile(r"^\s*([0-9]+(?:,[0-9]+)*)\s*=>\s*(\w+)\s*(.*)$")
PAT_GAZ_RULE_LINE = re.compile(r"^\s*GAZETTEER\s*=>\s*(.*)$")
PAT_MACRO_LINE = re.compile(r"\s*([a-zA-Z0-9_]+)=(\S+)\s*$")
PAT_SUBST = re.compile(r"{{\s*[a-zA-Z0-9_]+\s*}}")

GroupNumber = namedtuple("GroupNumber", ["n"])

GLOBALS = {f"G{i}": GroupNumber(i) for i in range(99)}

Rule = namedtuple("Rule", ["pattern", "actions"])

# Note: groupnumbers is none for the (single) Action we get for a GAZETTEER rule.
Action = namedtuple("Action", ["groupnumbers", "typename", "features"])


def one_or(someiterator: Iterable, default: Any = None) -> Any:
    """Return the next element in the iterator or the defaul value if there is no next element."""
    for el in someiterator:
        return el
    return default


def subst(strg: str, substs: Optional[Dict]) -> str:
    """
    Substitute any predefined replacements in the strg. If the strg contains sometime {{name}} and
    "name" is a key in substs, the "{{name}}" substring gets replaced with the value in substs.
    If the name is not in substs, the string remains unchanged. If the replacement string has placeholders,
    they get recursively substituted too.

    Args:
        strg: some string
        substs: dictionary of name->replacementstring or None

    Returns:
        the modified string
    """
    if substs is None or len(substs) == 0:
        return strg
    matches = list(re.finditer(PAT_SUBST, strg))
    if len(matches) == 0:
        return strg
    lastidx = 0
    parts = []
    for m in matches:
        start, end = m.span()
        txt = m.group()
        var = txt[2:-2]
        val = substs.get(var)
        if val is not None:
            val = "(?:" + str(val) + ")"
            txt = subst(str(val), substs)
        if start > lastidx:
            parts.append(strg[lastidx:start])
        parts.append(txt)
        lastidx = end
    if lastidx < len(strg):
        parts.append(strg[lastidx:])
    ret = "".join(parts)
    return ret


def replace_group(feats: Dict, groups: Union[list, tuple]):
    """Replace any group placeholders in any of the feats with the text from the group in the match"""
    ret = {}
    for k, v in feats.items():
        if isinstance(v, GroupNumber):
            v = groups[v.n][2]  # each group is a tuple start, end, text
        ret[k] = v
    return ret


class StringRegexAnnotator(GazetteerBase):
    """
    An annotator for finding matches for any number of complex regular expression rules in a document.
    """
    def __init__(self,
                 source=None, source_fmt="file",
                 string_gazetteer=None,
                 outset_name="",
                 annset_name="",
                 containing_type=None,
                 list_features=None,
                 skip_longest=False,
                 longest_only: bool = False,
                 select_rules="all",  # or first / last
                 regex_module='re',
                 start_type: Optional[str] = None,
                 end_type: Optional[str] = None,
                 split_type: Optional[str] = None,
                 ):
        """
        Create a StringRegexAnnotator and optionally load regex patterns.

        Args:
            source: where to load the regex rules from, format depends on source_fmt. If None, nothing is loaded.
            source_fmt: the format of the source. Either "rule-list" for a list of Rule instances,
                or "file" in which case the rules are loaded from a file with that path
                or "string" in which case the rules are loaded from the given string.
            outset_name: name of the output annotation set
            string_gazetteer: an initialized instance of StringGazetteer, if specified, will be used for GAZETTEER
                rules. If not specified, no GAZETTEER rules are allowed.
            annset_name: the input annotation set if matching is restricted to spans covered by
                containing annotations.
            containing_type: if this is not None, then matching is restricted to spans covered by annotations
                of this type. The annotations should not overlap.
            list_features: a dictionary of arbitrary default features to add to all annotations created
                for matches from any of the rules loaded from the current source
            skip_longest: if True, after a match, the next match is attempted after the longest current
                match. If False, the next match is attempted at the next offset after the start of the
                current match.
            longest_only: if True, only use the longest match(es) of all matches
            select_rules: the strategy of which rules select from all that have acceptable matches.
                One of: "all": apply all matching rules (all matching or all longest depending on longest_only)
                "first": apply the first of all matching/first of all longest matching rules
                "last": apply the last of all matching/all longest matching rules
            regex_module: the name (string) of the regular expression module to use. Currently either
                "re" or "regexp" to use the module with the corresponding name. Only the module
                used is attempted to get loaded.
            start_type: if not None, the annotation type of annotations defining possible starting points of matches,
                if None, matches can occur anywhere
            end_type: if not None, the annotation type of annotations defining possible end points of matches, if
                None, matches can end anywhere
            split_type: the annotation type of annotations indicating splits, no match can cross a split
        """
        self.rules = []
        self.outset_name = outset_name
        self.annset_name = annset_name
        self.containing_type = containing_type
        self.skip_longest = skip_longest
        self.longest_only = longest_only
        self.select_rules = select_rules
        self.regex_module = regex_module
        self.start_type = start_type
        self.end_type = end_type
        self.split_type = split_type
        self.list_features = list_features
        self.gazetteer = string_gazetteer
        if regex_module == "regex":
            try:
                import regex
                self.re = regex
            except Exception as ex:
                raise Exception(f"Cannot use module regex, import failed", ex)
        else:
            self.re = re
        self.features4list = []
        if source is not None:
            self.append(source, source_fmt=source_fmt, list_features=list_features)

    def make_rule(self,
                  pats: Union[str, List[str]],
                  acts: List[Tuple[str, str, dict]],
                  substs: Optional[Dict] = None,
                  list_features: Optional[Dict] = None,
                  ):
        """
        Create a rule representation from a pattern string or list of pattern strings, an a list of action line tuples
        (groupnumbersstring, typenamestring, featureassignmentsstring) and a dictionary of name substitutions.
        Alternately, the pats parameter could be the instance of a gazetteer.

        Each featureassignmentsstring is a string of the form "fname1=fval1, fname2=fval2".

        Args:
            pats: a list of pattern strings, or a single pattern string, or a gazetteer instance
            acts: list of tuples (groupnumbersstring, typenamestring, features)
            substs: dictionary of name -> string substituions
            list_features: features to add to each action, if None, add the ones specified at init time

        Returns:
            a Rule instance
        """
        if list_features is None:
            list_features = self.list_features
            if list_features is None:
                list_features = {}
        if isinstance(pats, str):
            pats = subst(pats.strip(), substs)
        elif isinstance(pats, list):
            # pats = ["(?:" + subst(p.strip(), substs) + ")" for p in pats]
            pats = ["(?:"+subst(p.strip()+")", substs) for p in pats]
        elif isinstance(pats, GazetteerBase):
            pattern = pats
        else:
            raise Exception(f"Parameter pats neither a string, list of strings or gazetteer instance but {type(pats)}")
        if isinstance(pats, list):
            pattern_string = "|".join(pats)
            try:
                pattern = self.re.compile(pattern_string)  # noqa: F821
            except Exception as ex:
                raise Exception(f"Problem in pattern {pattern_string}", ex)
        anndescs = []
        for act in acts:
            grpnrs, typname, feats = act
            grpnrs = [int(x) for x in grpnrs.strip().split(",")]
            fassignments = list_features.copy()
            fassignments.update(feats)
            anndescs.append(Action(groupnumbers=grpnrs, typename=typname, features=fassignments))
        return Rule(pattern=pattern, actions=anndescs)

    def append(self, source: Union[str, List], source_fmt: str = "file", list_features = None):
        """
        Load a list of rules.

        Args:
            source: where/what to load. See the init parameter description.
            source_fmt: the format of the source, see the init parameter description.
            list_features: if not None a dictionary of features to assign to annotations created
                for any of the rules loaded by that method call.
        """
        if list_features is None:
            list_features = self.list_features
        if source_fmt == "rule-list":
            for rule in source:
                self.rules.append(rule)
        else:
            if source_fmt == "file":
                with open(source, "rt", encoding="utf-8") as infp:
                    lines = infp.readlines()
            elif source_fmt == "string":
                lines = source.split("\n")
            else:
                raise Exception(f"Unknown source format: {source_fmt}")
            cur_pats = []  # for each line, the original pattern string gets appended
            cur_acts = []  # for each line, a tuple with group list string, typename string, feature assign string
            cur_substs = {}
            for line in lines:
                line = line.rstrip("\n\r")
                line = line.strip()
                if line == "":
                    continue
                if line.startswith("//") or line.startswith("#"):
                    continue  # comment line
                if line.startswith("|"):
                    # if there is a current rule, add it
                    if len(cur_acts) > 0:
                        # finish and add rule
                        rule = self.make_rule(cur_pats, cur_acts, substs=cur_substs, list_features=list_features)
                        cur_acts = []
                        cur_pats = []
                        self.rules.append(rule)
                    # pattern line
                    cur_pats.append(line[1:].strip())
                    continue
                if line.startswith("+"):
                    # if there is a current rule, add it
                    if len(cur_acts) > 0:
                        # finish and add rule
                        rule = self.make_rule(cur_pats, cur_acts, substs=cur_substs, list_features=list_features)
                        cur_acts = []
                        cur_pats = []
                        self.rules.append(rule)
                    # pattern line: if we have already something in cur_pats, concatenate this to the last pat we have
                    # otherwise, add a new line
                    if len(cur_pats) == 0:
                        cur_pats.append(line[1:].strip())
                    else:
                        cur_pats[-1] = cur_pats[-1] + line[1:].strip()
                    continue
                mo = re.match(PAT_RULE_BODY_LINE, line)
                if mo is not None:
                    grouplist, typename, featureassignments = mo.groups()
                    # now try to match the feature assignments as the initializer of a dict, if that works,
                    # it is a proper line, otherwise we get an error
                    try:
                        features = eval("dict("+featureassignments+")", GLOBALS)
                    except Exception as ex:
                        raise Exception(f"Not a valid feature assignment: {featureassignments}", ex)
                    cur_acts.append((grouplist, typename, features))
                    continue
                mo = re.fullmatch(PAT_GAZ_RULE_LINE, line)
                if mo is not None:
                    if self.gazetteer is None:
                        raise Exception("GAZETTEER rule found but no gazetteer specified for StringRegexAnnotator")
                    if len(cur_acts) > 0:
                        # finish and add rule
                        rule = self.make_rule(cur_pats, cur_acts, substs=cur_substs, list_features=list_features)
                        cur_acts = []
                        cur_pats = []
                        self.rules.append(rule)
                    featureassignments = mo.groups()[0]
                    try:
                        features = eval("dict("+featureassignments+")", GLOBALS)
                    except Exception as ex:
                        raise Exception(f"Not a valid feature assignment: {featureassignments}", ex)
                    self.rules.append(
                        self.make_rule(self.gazetteer, [("0", "DUMMY-NOT-USED", features)],
                                       substs=None, list_features=list_features))
                    continue
                mo = re.fullmatch(PAT_MACRO_LINE, line)
                if mo is not None:
                    name = mo.group(1)
                    pat = mo.group(2)
                    cur_substs[name] = pat
                    continue
                # if we fall through to here, the line does not match anything known, must be an error
                raise Exception(f"Odd line: {line}")
            # end for line
            if cur_acts:
                # finish and add rule
                rule = self.make_rule(cur_pats, cur_acts, substs=cur_substs, list_features=list_features)
                self.rules.append(rule)
            else:
                # if there was no last rule, and if rules is still empty, complain
                if len(self.rules) == 0:
                    raise Exception("No complete rule found")

    def match_next(self, pat: Any, text: str,
                   from_offset: int = 0,
                   add_offset: int = 0,
                   start_offsets: Union[None, list, set] = None,
                   end_offsets: Union[None, list, set] = None,
                   split_offsets: Union[None, list, set] = None
                   ):
        """
        Find the next metch for the compiled pattern in text, at or after from_offset, but only if
        all of the start/end/split offset limitations are satisfied (if present).

        The from_offset is the offset within text, while add_offset is an additional offset value
        to get added so we can compare to any of the start_offsets, end_offsets, split_offsets
        (because text may just be a substring of the full text to which those offsets refer).

        Args:
            pat: a pre-compiled re/regex pattern or the gazetteer object for a gazetteer rule
            text: the text in which to search for the pattern
            from_offset: the offset in text from which on to search for the pattern
            add_offset: this gets added to a match offset in order to be comparable to the start/end/split offsets
            start_offsets: a set/list of offsets where a match must start
            end_offsets: a set/list of offsets where a match must end
            split_offsets: a set/list of offsets where a match cannot cross

        Returns:
            None if no match is found, otherwise, if pat is a regex,
            a tuple (start, end, groups, False) where groups is a tuple/list with all
            groups from the RE, starting with group(0), then group(1) etc. Each group in turn as a tuple
            (start, end, text).
            If pat is a gezetter, a tuple (start, end, matches, True) where matches is the list of matches returned
            from the gazetteer find method.
        """
        if isinstance(pat, StringGazetteer):
            # use the gazetteer to find the next match(es) in the text, starting at the given offset
            # Note: this sets longest_only to None to use whatever is configured for the StringGazetteer
            # The annotatation type will also be determined by that gazetteer, while the offsets are determined
            # by what is defined in this StringRegexAnnotator
            matches, maxlen, where = pat.find(text, start=from_offset, longest_only=False,
                                              start_offsets=start_offsets, end_offsets=end_offsets,
                                              split_offsets=split_offsets)
            if maxlen == 0:
                return None
            else:
                return where, where+maxlen, matches, True
        m = self.re.search(pat, text[from_offset:])
        while m:
            # in this loop we return the first match that is valid, iterating until we find one or
            # no more matches are found
            lastidx = m.lastindex
            if lastidx is None:
                lastidx = 0
            groups = [(m.start(i)+from_offset, m.end(i)+from_offset, m.group(i)) for i in range(lastidx+1)]
            start, end = [o+from_offset for o in m.span()]

            ostart = start + add_offset
            oend = end + add_offset
            if start_offsets and ostart not in start_offsets:
                continue
            if end_offsets and oend not in end_offsets:
                continue
            if split_offsets:
                for i in range(ostart, oend):
                    if i in split_offsets:
                        continue
            # the match should be valid, return it
            return start, end, groups, False
        # end while
        return None

    def find_all(self, text: str,
                 start: int = 0,
                 add_offset: int = 0,
                 longest_only: Union[None, bool] = None,
                 skip_longest: Union[None, bool] = None,
                 select_rules: Union[None, str] = None,
                 start_offsets: Union[List, Set, None] = None,
                 end_offsets: Union[List, Set, None] = None,
                 split_offsets: Union[List, Set, None] = None):
        """
        Find all matches for the rules in this annotator and satisfying any addition constraints specified through
        the parameters.

        Args:
            text: string to search
            start: offset where to start searching (0)
            add_offset: what to add to compare the within-text offsets to the offsets in start_offsets etc. This is
                used when text is a substring of the original string to match and the start_offsets refer to offsets
                in the original string.
            longest_only: if True, return only the longest match at each position, if None use gazetteer setting
            skip_longest: if True, find next match after longest match, if None use gazetteer setting
            select_rules: if not None, overrides the setting from the StringRegexAnnotator instance
            start_offsets: if not None, a list/set of offsets where a match can start
            end_offsets: if not None, a list/set of offsets where a match can end
            split_offsets: if not None, a list/set of offsets which are considered split locations

        Yields:
            each of the matches
        """
        # first of all create a list of match iterator generators that correspond to each of the rules
        if longest_only is None:
            longest_only = self.longest_only
        if skip_longest is None:
            skip_longest = self.skip_longest
        if select_rules is None:
            select_rules = self.select_rules
        beyond = len(text)+1

        # initialize the matches
        curoff = start
        matches = [self.match_next(rule.pattern, text, from_offset=start, add_offset=add_offset,
                                   start_offsets=start_offsets, end_offsets=end_offsets,
                                   split_offsets=split_offsets) for rule in self.rules]

        result = []
        finished = False   # set to true once all matches are None, i.e. there is no match for any pattern left
        while not finished and curoff < len(text):
            longestspan = 0
            smallestoff = beyond
            # find the smallest offset of all matches, and also the length of the longest span among all smallestoff
            # matches
            for idx, match in enumerate(matches):
                # if the match is starting before curoff, update it
                if match and match[0] < curoff:
                    match = self.match_next(self.rules[idx].pattern, text,
                                            from_offset=curoff, add_offset=add_offset,
                                            start_offsets=start_offsets, end_offsets=end_offsets,
                                            split_offsets=split_offsets)
                    matches[idx] = match
                if not match:
                    continue
                # if there actually is a valid match, use it to determine the smallest offset and the longest match len
                if match[0] < smallestoff:
                    # new smallest offset, also need to reset the longest match
                    smallestoff = match[0]
                    longestspan = match[1] - match[0]
                if match[0] <= smallestoff:
                    mlen = match[1] - match[0]
                    if mlen > longestspan:
                        longestspan = mlen
            # for
            # we now know where the next match(es) is/are happening and what the longest match(es) is/are
            if smallestoff == beyond:
                # no (more) matches found, break out of the while
                break
            curoff = smallestoff
            # we have at least one match still at smallestoff
            # depending on the strategy, select the rule to match:
            # all: all rules starting at smallestoff
            # first: the first rule at smallestoff
            # last: the last rule at smallestoff
            # firstlongest: the first rule at smallestoff which is of maximum length
            # We select the indices of all rules for which the match should get considered
            idx2use = []
            lastidx = None
            for idx, match in enumerate(matches):
                if not match:
                    continue
                matchlen = match[1] - match[0]
                if match[0] != smallestoff:
                    continue
                if not longest_only and select_rules == "all":
                    idx2use.append(idx)
                elif longest_only and select_rules == "all" and matchlen == longestspan:
                    idx2use.append(idx)
                elif not longest_only and select_rules == "first":
                    idx2use.append(idx)
                    break
                elif longest_only and select_rules == "first" and matchlen == longestspan:
                    idx2use.append(idx)
                    break
                elif not longest_only and select_rules == "last":
                    lastidx = idx
                elif longest_only and select_rules == "last" and matchlen == longestspan:
                    lastidx = idx
            # end for
            if select_rules == "last":
                idx2use.append(lastidx)
            # now we have the list of idxs for which to add a match to the result
            for idx in idx2use:
                match = matches[idx]
                # check if we got a match that corresponds to a gazetteer rule, in that case, just
                # use the matches we got from there.
                if match[3]:
                    for m in match[2]:
                        # we need to splice in the features from the rule, if necessary
                        act = self.rules[idx].actions[0]   # for GAZETTEER rules, there is always only one act exactly
                        if len(act.features) > 0:
                            features = {}
                            features.update(m.features)
                            features.update(act.features)
                            m.features = features
                        # result.append(m)
                        yield m
                    continue
                acts = self.rules[idx].actions
                groups = match[2]
                for act in acts:
                    feats = replace_group(act.features, groups)
                    for gnr in act.groupnumbers:
                        toadd = Match(start=groups[gnr][0],
                                      end=groups[gnr][1],
                                      match=groups[gnr][2],
                                      features=feats,
                                      type=act.typename)
                        # result.append(toadd)
                        yield toadd
            # end for
            # now depending on skip_longest, skip either one offset or the length of the longest match
            if skip_longest:
                curoff += longestspan
            else:
                curoff += 1
        # end while

    def __call__(self, doc: Document, **kwargs):
        outset = doc.annset(self.outset_name)
        annset = doc.annset(self.annset_name)
        chunks = []  # list of tuples (text, startoffset)
        split_offsets = None
        if self.split_type is not None:
            split_offsets = set()
            anns = annset.with_type(self.split_type)
            for ann in anns:
                for i in range(ann.start, ann.end):
                    split_offsets.add(i)
        start_offsets = None
        end_offsets = None
        if self.start_type is not None:
            start_offsets = set()
            anns = annset.with_type(self.start_type)
            for ann in anns:
                start_offsets.add(ann.start)
        if self.end_type is not None:
            end_offsets = set()
            anns = annset.with_type(self.end_type)
            for ann in anns:
                end_offsets.add(ann.end)
        if self.containing_type is not None:
            for ann in annset.with_type(self.containing_type):
                chunks.append((doc[ann], ann.start))
        else:
            chunks.append((doc.text, 0))
        for chunk in chunks:
            text = chunk[0]
            offset = chunk[1]
            # find the matches, add annotations, with the offsets adapted by offset
            matches = self.find_all(text=text, add_offset=offset, start_offsets=start_offsets, end_offsets=end_offsets,
                                    split_offsets=split_offsets)
            for match in matches:
                outset.add(match.start + offset, match.end + offset, match.type, match.features)
        return doc
