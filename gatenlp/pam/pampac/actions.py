"""
Module for PAMPAC action classes.
"""
from abc import ABC, abstractmethod
from typing import List, Union
from gatenlp import Annotation
from gatenlp.features import Features


class Getter(ABC):
    """
    Common base class of all Getter helper classes.
    """
    @abstractmethod
    def __call__(self, succ, context=None, location=None):
        pass


def _get_match(succ, name, resultidx=0, matchidx=0, silent_fail=False):
    """
    Helper method to return the match info for the given result index and name, or None.

    Args:
        succ: success instance
        name: name of the match info
        resultidx: index of the result in success
        matchidx: if there is more than one matching match info with that name, which one to return
        silent_fail: if True, return None, if False, raise an exception if the match info is not present

    Returns:
        the match info or None

    """
    if resultidx >= len(succ):
        if not silent_fail:
            raise Exception(f"No resultidx {resultidx}, only {len(succ)} results")
        return None
    res = succ[resultidx]
    matches = res.matches4name(name)
    if not matches:
        if not silent_fail:
            raise Exception(f"No match info with name {name} in result")
        return None
    if matchidx >= len(matches):
        if not silent_fail:
            raise Exception(f"No match info with index {matchidx}, length is {len(matches)}")
        return None
    return matches[matchidx]


# pylint: disable=R0912
def _get_span(succ, name, resultidx=0, matchidx=0, silent_fail=False):
    """
    Helper method to return the span for the given result index and name, or None.

    Args:
        succ: success instance
        name: name of the match info, if None, uses the entire span of the result
        resultidx: index of the result in success
        matchidx: if there is more than one match info with that name, which one to return, if no name, ignored
        silent_fail: if True, return None, if False, raise an exception if the match info is not present

    Returns:
        the span or None if no Span exists
    """
    if resultidx >= len(succ):
        if not silent_fail:
            raise Exception(f"No resultidx {resultidx}, only {len(succ)} results")
        return None
    res = succ[resultidx]
    if name:
        matches = res.matches4name(name)
        if not matches:
            if not silent_fail:
                raise Exception(f"No match info with name {name} in result")
            return None
        if matchidx >= len(matches):
            if not silent_fail:
                raise Exception(f"No match info with index {matchidx}, length is {len(matches)}")
            return None
        ret = matches[matchidx].get("span")
    else:
        ret = res.span
    if ret is None:
        if silent_fail:
            return None
        else:
            raise Exception("No span found")
    return ret


class Actions:
    """
    A container to run several actions for a rule.
    """

    def __init__(self,
                 *actions,
                 ):
        """
        Wrap several actions for use in a rule.

        Args:
            *actions: any number of actions to run.
        """
        self.actions = list(actions)

    def __call__(self, succ, context=None, location=None, annset=None):
        """
        Invokes the actions defined for this wrapper in sequence and
        returns one of the following: for no wrapped actions, no action is invoked and None is returned;
        for exactly one action the return value of that action is returned, for 2 or more actions
        a list with the return values of each of those actions is returned.

        Args:
            succ:  the success object
            context: the context
            location:  the location
            annset: an annotation set to use for the actions, this is only used for some actions and
                getting ignored by most others.

        Returns: None, action return value or list of action return values

        """
        if len(self.actions) == 1:
            return self.actions[0](succ, context=context, location=location, annset=annset)
        elif len(self.actions) == 0:
            return None
        else:
            ret = []
            for action in self.actions:
                ret.append(action(succ, context=context, location=location, annset=annset))
            return ret

    def add(self, action, tofront=False):
        """
        Add an action to the list of existing actions.

        Args:
            action: the action to add
            tofront: if True, add as first instead of last action
        """
        if tofront:
            self.actions.insert(0, action)
        else:
            self.actions.append(action)


class AddAnn:
    """
    Action for adding an annotation.
    """

    def __init__(
            self,
            name=None,
            ann=None,  # create a copy of this ann retrieved with GetAnn
            type=None,  # or create a new annotation with this type
            annset_name=None,  # if not none, create in this set instead of the default output set
            features=None,
            span=None,  # use literal span, GetSpan, if none, span from match
            resultidx=0,
            matchidx=0,
            silent_fail=False,
    ):  # pylint: disable=W0622
        """
        Create an action for adding a new annotation to the outset.

        Args:
            name: the name of the match to use for getting the annotation span, if None, use the
                whole span of each match
            ann:  either an Annotation which will be (deep) copied to create the new annotation, or
                a GetAnn helper for copying the annoation the helper returns. If this is specified the
                other parameters for creating a new annotation are ignored.
            type: the type of a new annotation to create
            annset_name: if not None, create the new annotation in a set with this name instead of the
                default output set.
            features: the features of a new annotation to create. This can be a GetFeatures helper for copying
                the features from another annotation in the results
            span: the span of the annotation, this can be a GetSpan helper for copying the span from another
                annotation in the results
            resultidx: the index of the result to use if more than one result is in the Success. If None,
                the AddAnn action is performed for all results
            matchidx: the index of the match info to use if more than one item matches the given name. If None,
                the AddAnn action is performed for all match info items with that name.
            silent_fail: if True and the annotation can not be created for some reason, just do silently nothing,
                otherwise raises an Exception.
        """
        # span is either a span, the index of a match info to take the span from, or a callable that will return the
        # span at firing time
        assert type is not None or ann is not None
        self.name = name
        self.anntype = type
        self.ann = ann
        self.features = features
        self.span = span
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail
        self.annset_name = annset_name

    # pylint: disable=R0912
    def _add4span(self, span, succ, context, location):
        if span is None:
            return
        if self.annset_name is not None:
            outset = context.doc.annset(self.annset_name)
        else:
            outset = context.outset
        if self.ann:
            if isinstance(self.ann, Annotation):
                outset.add_ann(self.ann.deepcopy())
            else:
                ann = self.ann(succ)
                if ann is None:
                    if self.silent_fail:
                        return
                    else:
                        raise Exception("No matching annotation found")
                outset.add_ann(ann)
        else:
            if self.span:
                if callable(self.span):
                    span = self.span(succ, context=context, location=location)
                else:
                    span = self.span
            if callable(self.anntype):
                anntype = self.anntype(succ, context=context, location=location)
            else:
                anntype = self.anntype
            if self.features:
                if callable(self.features):
                    features = self.features(succ, context=context, location=location)
                else:
                    # NOTE: if we got a dictionary where some values are helpers, we need to run the helper
                    # and replace the value with the result. However, this would change the original dictionary
                    # just the first time if there are several matches, so we always shallow copy the features
                    # first!
                    features = self.features.copy()
                    for k, v in features.items():
                        if isinstance(v, Getter):
                            features[k] = v(succ, context=context, location=location)
            else:
                features = None
            outset.add(span.start, span.end, anntype, features=features)

    def _add4result(self, succ, resultidx, context, location):
        if self.matchidx is None:
            for matchidx in range(len(succ[resultidx].matches)):
                span = _get_span(succ, self.name, resultidx, matchidx, self.silent_fail)
                # print(f"DEBUG: midx=None, running for {matchidx}, span={span}")
                self._add4span(span, succ, context, location)
        else:
            span = _get_span(succ, self.name, resultidx, self.matchidx, self.silent_fail)
            # print(f"DEBUG: running for {self.matchidx}, span={span}")
            self._add4span(span, succ, context, location)

    def __call__(self, succ, context=None, location=None, annset=None):
        if self.resultidx is None:
            for resultidx in range(len(succ)):
                # print(f"DEBUG: ridx=None, running for {resultidx}")
                self._add4result(succ, resultidx, context, location)
        else:
            # print(f"DEBUG: running for {self.resultidx}")
            self._add4result(succ, self.resultidx, context, location)


class UpdateAnnFeatures:
    """
    Action for updating the features of an annotation.
    """

    def __init__(
            self,
            name=None,
            updateann=None,
            fromann=None,
            features=None,
            replace=False,  # replace existing features rather than updating
            resultidx=0,
            matchidx=0,
            silent_fail=False,
            deepcopy=False
    ):
        """
        Create an UpdateAnnFeatures action. The features to use for updating can either come from
        an existing annotation, an annotation fetched with a GetAnn annotation getter, or from a
        a features instance, a feature getter or a dictionary.

        Args:
            name: the name of the match to use for getting the annotation to modify (if updateann is not
                specified). This must be None if updateann is specified.
            updateann: if specified, update the features of this annotation. This can be either a literal
                annotation or a GetAnn help to access another annotation from the result.
            fromann: if specified use the features from this annotation. This can be either a literal annotation
                or a GetAnn helper to access another annotation from the result.
            features: the features to use for updating, either literal features or dictionary,
                or a GetFeatures helper.
            replace: if True, replace the existing features with the new ones, otherwise update the existing features.
            resultidx: the index of the result to use, if there is more than one (default: 0)
            matchidx: the index of a matching info element to use, if more than one matches exist
                with the given name (default: 0)
            silent_fail: if True, do not raise an exception if the features cannot be updated
            deepcopy: if True, existing features are deep-copied, otherwise a shallow copy or new instance
                is created.
        """
        # check parameters for getting the features:
        if fromann is None and features is None:
            raise Exception("Either fromann or features must be specified")
        if fromann is not None and features is not None:
            raise Exception("Parameters fromann and features must not be both specified at the same time")
        # check parameters for setting features:
        if name is None and updateann is None:
            raise Exception("Either name or updateann must be specified")
        if name is not None and updateann is not None:
            raise Exception("Parameters name and updateann must not be both specified at the same time")
        self.name = name
        self.updateann = updateann
        self.fromann = fromann
        self.replace = replace
        self.features = features
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail
        self.deepcopy = deepcopy

    # pylint: disable=R0912
    def __call__(self, succ, context=None, location=None, annset=None):
        # determine the annotation to modify
        if self.updateann is not None:
            if isinstance(self.updateann, Annotation):
                updateann = self.updateann
            else:
                updateann = self.updateann(succ, context=context, location=location)
        else:
            match = _get_match(
                succ, self.name, self.resultidx, self.matchidx, self.silent_fail
            )
            if not match:
                if self.silent_fail:
                    return
                else:
                    raise Exception(f"Could not find the name {self.name}")
            updateann = match.get("ann")
        if updateann is None:
            if self.silent_fail:
                return
            else:
                raise Exception(
                    f"Could not find an annotation for the name {self.name}"
                )
        updatefeats = updateann.features
        # determine the features to use: either from an annotation/annotation getter or from
        # features or a features getter

        if self.fromann is not None:
            if isinstance(self.fromann, Annotation):
                fromfeats = self.fromann.features
            else:
                ann = self.fromann(succ)
                if ann is None:
                    if self.silent_fail:
                        return
                    else:
                        raise Exception("No matching source annotation found")
                fromfeats = ann.features
        else:   # get it from self.features
            if callable(self.features):
                fromfeats = self.features(succ, context=context, location=location)
            else:
                fromfeats = self.features
        # make sure we have features and optionally make sure we have a deep copy
        fromfeats = Features(fromfeats, deepcopy=self.deepcopy)
        if self.replace:
            updatefeats.clear()
        updatefeats.update(fromfeats)


class RemoveAnn:
    """
    Action for removing an anntoation.
    """
    def __init__(self, name=None,
                 annset_name=None,
                 resultidx=0, matchidx=0,
                 silent_fail=True):
        """
        Create a remove annoation action.

        Args:
            name: the name of a match from which to get the annotation to remove
            annset_name: the name of the annotation set to remove the annotation from. If this is the same set
                as used for matching it may influence the matching result if the annotation is removed before
                the remaining matching is done.
                If this is not specified, the annotation set of the (first) input annotation is used.
            resultidx: index of the result to use, if several (default: 0)
            matchidx: index of the match to use, if several (default: 0)
            silent_fail: if True, silently ignore the error of no annotation to get removed
        """
        assert name is not None
        self.name = name
        assert annset_name is None or isinstance(annset_name, str), \
            f"annset_name must be a string or None but is {annset_name}"
        self.annset_name = annset_name
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None, annset=None):
        match = _get_match(
            succ, self.name, self.resultidx, self.matchidx, self.silent_fail
        )
        if not match:
            if self.silent_fail:
                return
            else:
                raise Exception(f"Could not find the name {self.name}")
        theann = match.get("ann")
        if theann is None:
            if self.silent_fail:
                return
            else:
                raise Exception(
                    f"Could not find an annotation for the name {self.name}"
                )
        if self.annset_name is not None:
            annset = context.doc.annset(self.annset_name)
        annset.remove(theann)


class RemoveAnnAll:
    """
    Remove all matching annotations from all results, if the binding name (if specified) and type name (if specified)
    matches.
    """

    def __init__(self,
                 names: Union[str, List[str]] = None,
                 types: Union[str, List[str]] = None,
                 annset_name: str = None,
                 silent_fail: bool = True):
        """
        Create a remove all annotation action. In order for an annotation to get removed it must match the given
        match name or one of the match names (if specified) AND match the given type name or one of the type names
        (if specified). If not match name and/or no type name is specified, the removal action is not restricted.

        Args:
            names: the name, or list of names, of a match(es) from which to get the annotation to remove.
            types: the annotation type, or list of types, of annotation within the whole matched pattern to remove
            annset_name: the name of the annotation set to remove the annotation from. If this is the same set
                as used for matching it may influence the matching result if the annotation is removed before
                the remaining matching is done.
                If this is not specified, the annotation set of the (first) input annotation is used.
            silent_fail: if True, silently ignore the error of no annotation to get removed
        """
        self.names = names
        self.types = types
        if names is not None:
            if isinstance(names, list):
                assert all(isinstance(c, str) for c in names), \
                    f"names must be a string or list of strings but is {names}"
            else:
                assert isinstance(names, str), \
                    f"names must be a string or list of strings but is {names}"
                self.names = [names]

        if types is not None:
            if isinstance(types, list):
                assert all(isinstance(c, str) for c in types), \
                    f"type must be a string or list of strings but is {types}"
            else:
                assert isinstance(types, str), \
                    f"types must be a string or list of strings but is {types}"
                self.types = [types]

        assert annset_name is None or isinstance(annset_name, str), \
            f"annset_name must be a string or None but is {annset_name}"
        self.annset_name = annset_name
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None, annset=None):

        anns_to_remove = set()

        for r in succ._results:

            # check all matches if the they fit the conditions
            for match in r.matches:
                ann = match.get("ann")
                if not ann:
                    continue
                if self.names is not None:
                    if match.get("name") not in self.names:
                        continue
                if self.types is not None:
                    if ann.type not in self.types:
                        continue
                anns_to_remove.add(ann)

        if not anns_to_remove:
            if self.silent_fail:
                return
            else:
                raise Exception(
                    f"Could not find annotations of type: {self.types} and / or of name: {self.names}"
                )

        if self.annset_name is not None:
            annset = context.doc.annset(self.annset_name)

        for ann in anns_to_remove:
            annset.remove(ann)
