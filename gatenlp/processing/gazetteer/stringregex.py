"""
Module that defines classes for matching annotators other than gazetteers which match e.g. regular expressions
of strings or annotations.
"""
import re
from typing import Union, List, Set
from collections import namedtuple
from gatenlp import Document
from gatenlp.processing.gazetteer.base import StringGazetteerBase, Match

# rule body line:
# one or more comma separated group numbers followed by a "=>" followed by feature assignments
# each feature assignment is a name followed by "=" followed by some non whitespace
# featuer assignments are comma-separated (whitespace can be added)
# e.g. 0,3 => Lookup f1=2, f2 = "something" , f3=True
PAT_RULE_BODY_LINE = re.compile(r"^\s*([0-9]+(?:,[0-9]+)*)\s*=>\s*(\w+)(\s*\w+\s*=\s*\S+)*\s*$")
PAT_RULE_BODY_FASSIGN = re.compile(r"\s*(\w+)\s*=\s*(\S+)")
PAT_DOLLARN = re.compile(r"^\$[0-9]+$")
PAT_MACRO_LINE = re.compile(r"\s*([a-zA-Z0-9_]+)=(\S+)\s*$")
PAT_SUBST = re.compile(r"{{\s*[a-zA-Z0-9_]+\s*}}")

GroupNumber = namedtuple("GroupNumber", ["n"])

def one_or(someiterator, default=None):
    for el in someiterator:
        return el
    return default

def subst(strg, substs):
    """
    Substitute any predefined replacements in the strg. If the strg contains sometime {{name}} and
    "name" is a key in substs, the "{{name}}" substring gets replaced with the value in substs.
    If the name is not in substs, the string remains unchanged. If the replacement string has placeholders,
    they get recursively substituted too.

    Args:
        strg: some string
        substs: dictionary of name->replacementstring

    Returns:
        the modified string
    """
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
            txt = subst(str(val), substs)
        if start > lastidx:
            parts.append(strg[lastidx:start])
        parts.append(txt)
        lastidx = end
    if lastidx < len(strg):
        parts.append(strg[lastidx:])
    ret = "".join(parts)
    return ret


def make_rule(pats, acts, substs, backend="re"):
    """
    Create a rule representation from a list of pattern strings, a list of action line tuples
    (groupnumber, typename, featureassignments) and a dictionary of name substitutions.

    Args:
        pats: list or pattern strings
        acts: list of tuples (groupnumber, typename, featureassignments)
        substs: dictionary of name -> string substituions

    Returns:
        a rule representation, a tuple where the first element is a compiled regexp and the second element
            is a list of of annotation descriptions.
            Each annotation description is a tuple with: list of group numbers, annotation type name,
            dictionary of featurename to value mappings. If the value is an instance of GroupNumber, then
            it represents the match group number to take the value of the feature from
    """
    pats = ["(?:"+subst(p.strip(), substs)+")" for p in pats]
    # TODO: use the correct backend!
    if backend == "re":
        pattern = re.compile("".join(pats))
    elif backend == "regex":
        pattern = regex.compile("".join(pats))
    else:
        raise Exception(f"Invalid regular expression backend: {backend}")
    anndescs = []
    for act in acts:
        grpnrs, typname, fstr = act
        grpnrs = [int(x) for x in grpnrs.strip().split(",")]
        fassignments = {}
        for m in re.findall(PAT_RULE_BODY_FASSIGN, fstr):
            fname, fval = m
            # ignore commas
            if fval.endswith(","):
                fval = fval[:-1]
            dollarn = re.match(PAT_DOLLARN, fval)
            if dollarn:
                fval = GroupNumber(int(fval[1:]))
            else:
                fval = eval(fval)
            fassignments[fname] = fval
        anndescs.append((grpnrs, typname, fassignments))
    return pattern, anndescs


class StringRegexAnnotator(StringGazetteerBase):
    """
    NOT YET IMPLEMENTED
    """
    def __init__(self,
                 source=None, source_fmt="file",
                 outset_name="",
                 annset_name="",
                 containing_type=None,
                 list_features=None,
                 skip_longest=False,
                 match="all",
                 engine='re'
                 ):
        """
        Create a StringRegexAnnotator and optionally load regex patterns.

        Args:
            source: where to load the regex rules from, format depends on source_fmt. If None, nothing is loaded.
            source_fmt: the format of the source. Either "list" for a list of tuples, where the first element
                is a compiled regular expression and the second element is a list of annotation descriptions.
                Each annotation description is a tuple with: list of group numbers, annotation type name,
                dictionary of featurename to value mappings. If the value is an instance of GroupNumber, then
                it represents the match group number to take the value of the feature from
                Or the source_fmt can be "file" in which case the rules are loaded from a file with that path.
                Or the source_fmt can be "string" in which case the rules are loaded from the given string.
            outset_name: name of the output annotation set
            annset_name: the input annotation set if matching is restricted to spans covered by
                containing annotations.
            containing_type: if this is not None, then matching is restricted to spans covered by annotations
                of this type. The annotations should not overlap.
            list_features: a dictionary of arbitrary default features to add to all annotations created
                for matches from any of the rules loaded from the current source
            skip_longest: if True, after a match, the next match is attempted after the longest current
                match. If False, the next match is attempted at the next offset after the start of the
                current match.
            match: the strategy of which rule to apply. One of: "all": apply all matching rules.
                "first": apply the first matching rule, do not attempt any others. "firstlongest":
                try all rules, apply the first of all rules with the longest match. "alllongest":
                try all rules, apply all rules with the longest match.
            engine: identifies which Python regular expression engine to use. Currently either
                "re" or "regexp" to use the package with the corresponding name. Only the package
                used is attempted to get loaded.
        """
        self.rules = []
        self.outset_name = outset_name
        self.annset_name = annset_name
        self.containing_type = containing_type
        self.skip_longest = skip_longest
        self.match = match
        self.engine = engine
        if engine == "regex":
            try:
                import regex
            except Exception as ex:
                raise Exception(f"Cannot use regex, import failed")
        self.features4list = []
        if source is not None:
            self.append(source, source_fmt=source_fmt, list_features=list_features)

    def add(self, rule, list_features=None):
        """
        Add a single rule.

        Args:
            rule: a tuple, where the first element
                is a compiled regular expression and the second element is a list of annotation descriptions.
                Each annotation description is a tuple with: list of group numbers, annotation type name,
                dictionary of featurename to value mappings. If the value is an instance of GroupNumber, then
                it represents the match group number to take the value of the feature from
            list_features: a dictionary of features to add to the rule
        """
        pat, anndescs = rule
        if list_features is not None:
            newdescs = []
            for anndesc in anndescs:
                grpnrs, typename, feats = anndesc
                features = list_features.copy()
                features.update(feats)
                newdescs.append((grpnrs, typename, features))
            anndescs = newdescs
        self.rules.append((pat, anndescs))

    def append(self, source, source_fmt="file", list_features=None):
        """
        Load a list of rules.

        Args:
            source: where/what to load. See the init parameter description.
            source_fmt: the format of the source, see the init parameter description.
            list_features: if not None a dictionary of features to assign to annotations created
                for any of the rules loaded by that method call.
        """
        # Format of rule: a tuple where the first element is a compiled regular expression
        # and the second element is a tuple. That tuple describes the
        # annotations to create for a match. The first element of the tuple is the annotation type or None
        # to use the out_type. The second element is a dictionary mapping each group number of the match
        # to a dictionary of features to assign. If the feature value is the string "$n" with n a group
        # number, then the value for that match group is used.
        if source_fmt == "list":
            for rule in source:
                self.add(rule, list_features=list_features)
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
                        rule = make_rule(cur_pats, cur_acts, cur_substs, backend=self.engine)
                        cur_acts = []
                        self.add(rule, list_features=list_features)
                    # pattern line
                    cur_pats.append(line[1:])
                    continue
                mo = re.match(PAT_RULE_BODY_LINE, line)
                if mo is not None:
                    grouplist, typename, featureassignments = mo.groups()
                    cur_acts.append((grouplist, typename, featureassignments))
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
                rule = make_rule(cur_pats, cur_acts, cur_substs, backend=self.engine)
                self.add(rule, list_features=list_features)
                pass
            else:
                # if there was no last rule, there was no rule at all, this is invalid
                raise Exception("No complete rule found")

    def find_all(self, text: str,
                 longest_only: Union[None, bool] = None,
                 skip_longest: Union[None, bool] = None,
                 start_offsets: Union[List, Set, None] = None,
                 end_offsets: Union[List, Set, None] = None,
                 ws_offsets: Union[List, Set, None] = None,
                 split_offsets: Union[List, Set, None] = None):
        # first of all create a list of match iterator generators that correspond to each of the rules
        BEYOND = len(text)+1
        if self.engine == "regex":
            # note: this should have been imported in the constructor, if needed
            module = regex   # noqa: E821
        else:
            module = re
        gens = [module.finditer(rule[0], text) for rule in self.rules]
        # create a list of matches or None for each of the generators
        matches = [one_or(gen) for gen in gens]

        curoff = 0
        result = []
        while curoff < len(text):
            # go through all matches (or None) in rule order: ignore the Nones these are done
            # if we got a match that is smaller than where we already are, consume until we get one at the curoff
            # or beyond. Every time we got a match at curoff or beyond, check which offset is the smallest. Also
            # update the current longest match length.
            # NOTE: if smallestoff is still len(text)+1 after this, we did not find any match!
            longestspan = 0
            smallestoff = BEYOND
            for idx, match in enumerate(matches):
                if match:
                    if match.span[0] < curoff:
                        match = one_or(gens[idx])
                        while match and match.span[0] < curoff:
                            match = one_or(gens[idx])
                        matches[idx] = match
                        if match is None:
                            continue
                    # we have a match for that rule
                    if match.span[0] < smallestoff:
                        # new smallest offset, also need to reset the longest match
                        smallestoff = match.span[0]
                        longestspan = 0
                    mlen = match.span[1] - match.span[0]
                    if mlen > longestspan:
                        longestspan = mlen
                # if match
            # for
            if smallestoff == BEYOND:
                # no (more) matches found, break out of the while
                break
            # we have at least one match still at smallestoff
            # depending on the strategy, select the rule to match:
            # all: all rules starting at smallestoff
            # first: the first rule at smallestoff
            # last: the last rule at smallestoff
            # firstlongest: the first rule at smallestoff which is of maximum length
            idx2use = []
            lastidx = None
            for idx, match in enumerate(matches):
                if match.span[0] != smallestoff:
                    continue
                if self.match == "all":
                    idx2use.append(idx)
                elif self.match == "first":
                    idx2use.append(idx)
                    break
                elif self.match == "firstlongest" and match.span[1]-match.span[0] == longestspan:
                    idx2use.append(idx)
                elif self.match == "last":
                    lastidx = idx
            # end for
            if self.match == "last":
                idx2use.append(lastidx)
            # now we have the list of idxs for which to add a match to the result
            for idx in idx2use:
                match = matches[idx]
                acts = self.rules[idx][1]
                for act in acts:
                    typename = act[0]
                    # TODO: replace GroupNumber
                    feats = act[1]
                    toadd = Match(match.span[0], match.span[1], text[match.span[0]:match.span[1]], typename, feats)
                    result.append(toadd)
            # end for
        # end while
        return result


    def __call__(self, doc: Document, **kwargs):
        chunks = []  # list of tuples (text, startoffset)
        if self.containing_type is not None:
            for ann in doc.annset(self.annset_name).with_type(self.containing_type):
                chunks.append((doc[ann], ann.start))
        else:
            chunks.append((doc.text, 0))
        for chunk in chunks:
            text = chunk[0]
            offset = chunk[1]
            # find the matches, add annotations, with the offsets adapted by offset
        return doc

