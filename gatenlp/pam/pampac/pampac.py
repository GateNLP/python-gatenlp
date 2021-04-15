"""
Module for the Pampac class.

"""
from gatenlp.processing.annotator import Annotator
from gatenlp.pam.pampac.data import Location, Context
from gatenlp.pam.pampac.rule import Rule
from gatenlp.utils import init_logger


class Pampac:
    """
    A class for applying a sequence of rules to a document.
    """

    def __init__(self, *rules, skip="longest", select="first"):
        """
        Initialize Pampac.

        Args:
            *rules: one or more rules
            skip:  how proceed after something has been matched at a position. One of: "longest" to proceed
              at the next text offset after the end of the longest match. "next" to use a location with the highest
              text and annotation index over all matches. "one" to increment the text offset by one and adjust
              the annotation index to point to the next annotation at or after the new text offset.
              "once": do not advance after the first location where a rule matches. NOTE: if skipping depends on
              on the match(es), only those matches for which a rule fires are considered.
            select: which of those rules that match to actually apply, i.e. call the action part of the rule.
              One of: "first": try all rules in sequence and call only the first one that matches. "highest": try
              all rules and only call the rules which has the highest priority, if there is more than one, the first
              of those.
        """
        assert len(rules) > 0
        assert skip in ["one", "longest", "next", "once"]
        assert select in ["first", "highest", "all"]
        for r in rules:
            assert isinstance(r, Rule)
        self.rules = rules
        self.priorities = [r.priority for r in self.rules]
        self.max_priority = max(self.priorities)
        for idx, r in enumerate(rules):
            if r.priority == self.max_priority:
                self.hp_rule = r
                self.hp_rule_idx = idx
                break
        self.skip = skip
        self.select = select

    def set_skip(self, val):
        """
        Different way to set the skip parameter.
        """
        self.skip = val
        return self

    def set_select(self, val):
        """
        Different way to set the select parameter.
        """
        self.select = val
        return self

    def run(self, doc, annotations, outset=None, start=None, end=None, debug=False):
        """
        Run the rules from location start to location end (default: full document), using the annotation set or list.

        Args:
            doc: the document to run on
            annotations: the annotation set or iterable to use
            outset: the output annotation set. If this is a string, retrieves the set from doc
            start: the text offset where to start matching
            end: the text offset where to end matching

        Returns:
            a list of tuples (offset, actionreturnvals) for each location where one or more matches occurred
        """
        logger = init_logger(debug=debug)
        if isinstance(outset, str):
            outset = doc.annset(outset)
        ctx = Context(doc=doc, anns=annotations, outset=outset, start=start, end=end)
        returntuples = []
        location = Location(ctx.start, 0)
        while True:
            # try the rules at the current position
            cur_offset = location.text_location
            frets = []
            rets = dict()
            for idx, r in enumerate(self.rules):
                logger.debug(f"Trying rule {idx} at location {location}")
                ret = r.parse(location, ctx)
                if ret.issuccess():
                    rets[idx] = ret
                    logger.debug(f"Success for rule {idx}, {len(ret)} results")
                    if self.select == "first":
                        break
            # we now got all the matching results in rets
            # if we have at least one matching ...
            if len(rets) > 0:
                fired_rets = []
                # choose the rules to fire and call the actions
                if self.select == "first":
                    idx, ret = list(rets.items())[0]
                    logger.debug(f"Firing rule {idx} at {location}")
                    fret = self.rules[idx].action(ret, context=ctx, location=location)
                    frets.append(fret)
                    fired_rets.append(ret)
                elif self.select == "all":
                    for idx, ret in rets.items():
                        logger.debug(f"Firing rule {idx} at {location}")
                        fret = self.rules[idx].action(
                            ret, context=ctx, location=location
                        )
                        frets.append(fret)
                        fired_rets.append(ret)
                elif self.select == "highest":
                    for idx, ret in rets.items():
                        if idx == self.hp_rule_idx:
                            logger.debug(f"Firing rule {idx} at {location}")
                            fret = self.rules[idx].action(
                                ret, context=ctx, location=location
                            )
                            frets.append(fret)
                            fired_rets.append(ret)
                # now that we have fired rules, find out how to advance to the next position
                if self.skip == "once":
                    return frets
                elif self.skip == "once":
                    location = ctx.inc_location(location, by_offset=1)
                elif self.skip == "longest":
                    longest = 0
                    for ret in fired_rets:
                        for res in ret:
                            if res.location.text_location > longest:
                                longest = res.location.text_location
                    location.text_location = longest
                    location = ctx.update_location_byoffset(location)
                elif self.skip == "next":
                    for ret in fired_rets:
                        for res in ret:
                            if res.location.text_location > location.text_location:
                                location.text_location = res.location.text_location
                                location.ann_location = res.location.ann_location
                            elif (
                                res.location.text_location == location.text_location
                                and res.location.ann_location > location.ann_location
                            ):
                                location.ann_location = res.location.ann_location
                returntuples.append((cur_offset, frets))
            else:
                # we had no match, just continue from the next offset
                location = ctx.inc_location(location, by_offset=1)
            if ctx.at_endofanns(location) or ctx.at_endoftext(location):
                break
        return returntuples

    __call__ = run


class PampacAnnotator(Annotator):
    """
    Class for running a Pampac ruleset.
    """
    pass