"""
Module that defines classes for matching annotators other than gazetteers which match e.g. regular expressions
of strings or annotations.
"""
import re
from gatenlp import Document
from gatenlp.processing.gazetteer.base import StringGazetteerAnnotator

PAT_MACRO_LINE = re.compile(r" *([a-zA-Z0-9_]+)=(\S+)")

class StringRegexAnnotator(StringGazetteerAnnotator):
    """
    NOT YET IMPLEMENTED
    """
    def __init__(self, source=None, source_fmt="file",
                 outset_name="", out_type="Match",
                 annset_name="", containing_type=None,
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
                is a compiled regular expression and the second element is a tuple. That tuple describes the
                annotations to create for a match. The first element of the tuple is the annotation type or None
                to use the out_type. The second element is a dictionary mapping each group number of the match
                to a dictionary of features to assign. If the feature value is the string "$n" with n a group
                number, then the value for that match group is used.
                Or the source_fmt can be "file" in which case the rules are loaded from a file with that path.
            outset_name: name of the output annotation set
            out_type: default type for output annotations, if the type is not specified with the rule
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
        self.out_type = out_type
        self.annset_name = annset_name
        self.containing_type = containing_type
        self.skip_longest = skip_longest
        self.match = match
        self.engine = engine
        self.features4list = []
        if source is not None:
            self.append(source, source_fmt=source_fmt, list_features=list_features)

    def add(self, rule, list_features=None):
        """
        Add a single rule.

        Args:
            rule: a tuple where the first element is a compiled regular expression and the second
                element is a tuple that describes the annotations to create if a match occurs.
                The first element of that tuple is the annotation type or None
                to use the out_type. The second element is a dictionary mapping each group number of the match
                to a dictionary of features to assign. If the feature value is the string "$n" with n a group
                number, then the value for that match group is used.
        """
        pat, desc = rule
        outtype, features = desc
        if outtype is None:
            outtype = self.out_type
        features = features.copy()
        if list_features is not None:
            features.update(list_features)
        self.rules.append((pat, (outtype, features)))

    def append(self, source, source_fmt="file", list_features=None):
        """
        Load a list of rules.

        Args:
            source: where/what to load. See the init parameter description.
            source_fmt: the format of the source, see the init parameter description.
            list_features: if not None a dictionary of features to assign to annotations created
                for any of the rules loaded by that method call.
        """
        if source_fmt == "list":
            for rule in source:
                self.add(rule, list_features=list_features)
        else:
            with open(source, "rt", encoding="utf-8") as infp:
                cur_pats = []
                cur_body = None
                for line in infp:
                    line = line.rstrip("\n\r")
                    line = line.strip()
                    if line == "":
                        continue
                    if line.startswith("//") or line.startswith("#"):
                        continue  # comment line
                    if line.startswith("|"):
                        # if there is a current rule, add it
                        if cur_body is not None:
                            # finish and add rule
                            self.add(rule, list_features=list_features)
                            pass
                        # pattern line
                        # TODO
                        continue
                    mo = re.match(PAT_RULE_BODY)
                    if mo is not None:
                        # rule body line
                        # TODO
                        continue
                    mo = re.fullmatch(PAT_MACRO_LINE, line)
                    if mo is not None:
                        name = mo.group(1)
                        pat = mo.group(2)
                        # TODO
                        continue
                    # if we fall through to here, the line does not match anything known, must be an error
                    raise Exception(f"Odd line: {line}")
                # end for line
                if cur_body is not None:
                    # finish and add rule
                    self.add(rule, list_features=list_features)
                    pass
                else:
                    # if there was no last rule, there was no rule at all, this is invalid
                    raise Exception("No complete rule found")

    def find_all(self, text, start, end):
        # NOTE: this must be implemented for this gazetteer to be a proper StringGazetteer which
        # can be used by the FeatureGazetteer
        pass

    def __call__(self, doc: Document, **kwargs):
        pass

