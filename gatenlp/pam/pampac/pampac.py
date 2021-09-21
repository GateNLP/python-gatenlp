"""
Module for the Pampac class.
"""
import sys

from gatenlp.pam.pampac.data import Location, Context
from gatenlp.pam.pampac.rule import Rule
from gatenlp.annotation_set import AnnotationSet
from gatenlp.utils import init_logger
from gatenlp.processing.annotator import Annotator


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
        for rule_ in rules:
            assert isinstance(rule_, Rule)
        self.rules = rules
        self.priorities = [r.priority for r in self.rules]
        self.max_priority = max(self.priorities)
        for idx, rule_ in enumerate(rules):
            if rule_.priority == self.max_priority:
                self.hp_rule = rule_
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

    # pylint: disable=R0912, R0915
    def run(self,
            doc,
            annotations,
            outset=None, start=None, end=None, containing_anns=None, debug=False):
        """
        Run the rules from location start to location end (default: full document), using the annotation set or list.

        Args:
            doc: the document to run on
            annotations: the annotation set or iterable to use for matching.
            outset: the output annotation set. If this is a string, retrieves the set from doc
            start: the text offset where to start matching
            end: the text offset where to end matching
            containing_anns: if this is an AnnotationSet or iterable of annotations, the rules are applied to each
                span of each of the annotations in order, and only input annotations that are fully contained
                in that span are processed (default: None, use the whole document)
            debug: enable debug logging

        Returns:
            a list of tuples (offset, actionreturnvals) for each location where one or more matches occurred
        """
        logger = init_logger(debug=debug)
        if isinstance(outset, str):
            outset = doc.annset(outset)
        returntuples = []
        ctx = Context(doc=doc, anns=annotations, outset=outset, start=start, end=end)
        location = Location(ctx.start, 0)
        if containing_anns is not None:
            # in order to be able to get the contained annotations, we need to make sure the `annotations`
            # are in a set
            if not isinstance(annotations, AnnotationSet):
                containing_anns = AnnotationSet.create_from(containing_anns)
            for ann in containing_anns:
                if ann.length == 0:
                    continue
                span_anns = annotations.within(ann)
                ctx = Context(doc=doc, anns=span_anns, outset=outset, start=ann.start, end=ann.end)
                returntuples.extend(self._run4span(logger, ctx, location))
            return returntuples
        else:
            return self._run4span(logger, ctx, location)

    def _run4span(self, logger, ctx, location):
        # Runs on a single span using the given context and start location and returns a list of tuples with
        # offset and actionreturnvals for each location where a match or matches occured
        returntuples = []
        while True:  # pylint: disable=R1702
            # try the rules at the current position
            cur_offset = location.text_location
            frets = []
            rets = dict()
            for idx, rule_ in enumerate(self.rules):
                logger.debug("Trying rule %s at location %s", idx, location)
                ret = rule_.parse(location, ctx)
                if ret.issuccess():
                    rets[idx] = ret
                    logger.debug("Success for rule %s, %s results", idx, len(ret))
                    if self.select == "first":
                        break
            # we now got all the matching results in rets
            # if we have at least one matching ...
            if len(rets) > 0:
                fired_rets = []
                # choose the rules to fire and call the actions
                if self.select == "first":
                    idx, ret = list(rets.items())[0]
                    logger.debug("Firing rule %s at %s", idx, location)
                    fret = self.rules[idx].action(ret, context=ctx, location=location)
                    frets.append(fret)
                    fired_rets.append(ret)
                elif self.select == "all":
                    for idx, ret in rets.items():
                        logger.debug("Firing rule %s at %s", idx, location)
                        fret = self.rules[idx].action(
                            ret, context=ctx, location=location
                        )
                        frets.append(fret)
                        fired_rets.append(ret)
                elif self.select == "highest":
                    for idx, ret in rets.items():
                        if idx == self.hp_rule_idx:
                            logger.debug("Firing rule %s at %s", idx, location)
                            fret = self.rules[idx].action(
                                ret, context=ctx, location=location
                            )
                            frets.append(fret)
                            fired_rets.append(ret)
                # now that we have fired rules, find out how to advance to the next position
                if self.skip == "once":
                    return frets
                elif self.skip == "one":
                    # we need to advance to the offset AFTER the BEGINNING of the earliest match
                    old_t = location.text_location
                    old_a = location.ann_location
                    next_o = sys.maxsize
                    for ret in fired_rets:
                        for res in ret:
                            if res.span is not None and res.span.start < next_o:
                                next_o = res.span.start
                    location = ctx.inc_location(location, to_offset=next_o+1)
                    # print(f"********** LOCATION: fired={len(fired_rets)}: from {old_t}/{old_a} for {next_o} to {location.text_location}/{location.ann_location}")
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
    def __init__(self,
                 pampac,
                 ann_desc,
                 outset_name=None,
                 containing_anns_desc=None):
        """

        Args:
            pampac: a Pampac instances
            ann_desc: annotation specification for annotations to use as input. This can be a annotation set name,
                or a list of either annotation set names or tuples, where the first element is an annotation set
                name and the second element is either a type name or a list of type names. E.g. `[("", "Token")]`
                to get all annotations with type Token from the default set or or `[("", ["PER", "ORG"]), "Key"]`
                to get all annotations with type PER or ORG from the default set and all annotations from the Key
                set.
            outset_name: the name of the annotation set where to add output annoations
            containing_anns_desc: a specification of annotations to use for containing annotations. If specified,
                the Pampac instance will run pattern matching on each span that corresponds to a containing annotation.
                Containing annotations should not overlap. The outputs for each containing annotation are aggregated
                and returned. Default: do not use containing annotations and run for the whole document.
        """
        self.pampac = pampac
        self.ann_desc = ann_desc
        self.outset_name = outset_name
        self.containing_anns_desc = containing_anns_desc

    def __call__(self, doc, **kwargs):
        outset = doc.annset(self.outset_name)
        anns = doc.anns(self.ann_desc)
        if self.containing_anns_desc is not None:
            cont = doc.anns(self.containing_anns_desc)
        else:
            cont = None
        return self.pampac.run(doc, anns, outset=outset, containing_anns=cont)
