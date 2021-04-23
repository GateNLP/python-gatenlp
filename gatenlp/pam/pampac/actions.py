"""
Module for PAMPAC action classes.
"""
from copy import deepcopy
from gatenlp import Annotation


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
        else:
            return None
    res = succ[resultidx]
    matches = res.matches4name(name)
    if not matches:
        if not silent_fail:
            raise Exception(f"No match info with name {name} in result")
        else:
            return None
    if matchidx >= len(matches):
        if not silent_fail:
            raise Exception(f"No match info with index {matchidx}, length is {len(matches)}")
        else:
            return None
    return matches[matchidx]


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
        else:
            return None
    res = succ[resultidx]
    if name:
        matches = res.matches4name(name)
        if not matches:
            if not silent_fail:
                raise Exception(f"No match info with name {name} in result")
            else:
                return None
        if matchidx >= len(matches):
            if not silent_fail:
                raise Exception(f"No match info with index {matchidx}, length is {len(matches)}")
            else:
                return None
        ret = matches[matchidx].get("span")
    else:
        ret = res.span
    if ret is None:
        if silent_fail:
            return None
        else:
            raise Exception(f"No span found")
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
        self.actions = actions

    def __call__(self, succ, context=None, location=None):
        """
        Invokes the actions defined for this wrapper in sequence and
        returns one of the following: for no wrapped actions, no action is invoked and None is returned;
        for exactly one action the return value of that action is returned, for 2 or more actions
        a list with the return values of each of those actions is returned.

        Args:
            succ:  the success object
            context: the context
            location:  the location

        Returns: None, action return value or list of action return values

        """
        if len(self.actions) == 1:
            return self.actions[0](succ, context=context, location=location)
        elif len(self.actions) == 0:
            return None
        else:
            ret = []
            for action in self.actions:
                ret.append(action(succ, context=context, location=location))
            return ret


class AddAnn:
    """
    Action for adding an annotation.
    """

    def __init__(
        self,
        name=None,
        ann=None,  # create a copy of this ann retrieved with GetAnn
        type=None,  # or create a new annotation with this type
        annset=None,  # if not none, create in this set instead of the one used for matching
        features=None,
        span=None,  # use literal span, GetSpan, if none, span from match
        resultidx=0,
        matchidx=0,
        silent_fail=False,
    ):
        """
        Create an action for adding a new annotation to the outset.

        Args:
            name: the name of the match to use for getting the annotation span, if None, use the
                whole span of each match
            ann:  either an Annotation which will be (deep) copied to create the new annotation, or
                a GetAnn helper for copying the annoation the helper returns. If this is specified the
                other parameters for creating a new annotation are ignored.
            type: the type of a new annotation to create
            annset: if not None, create the new annotation in this set instead of the one used for matching
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
        self.annset = annset

    def _add4span(self, span, succ, context, location):
        if span is None:
            return
        if self.annset:
            outset = self.annset
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
                    features = self.features
            else:
                features = None
            outset.add(span.start, span.end, anntype, features=features)

    def _add4result(self, succ, resultidx, context, location):
        if self.matchidx is None:
            for matchidx in range(len(succ[resultidx].matches)):
                span = _get_span(succ, self.name, resultidx, matchidx, self.silent_fail)
                self._add4span(span, succ, context, location)
        else:
            span = _get_span(succ, self.name, resultidx, self.matchidx, self.silent_fail)
            self._add4span(span, succ, context, location)

    def __call__(self, succ, context=None, location=None):
        if self.resultidx is None:
            for resultidx in range(len(succ)):
                self._add4result(succ, resultidx, context, location)
        else:
            self._add4result(succ, self.resultidx, context, location)


class UpdateAnnFeatures:
    """
    Action for updating the features of an annotation.
    """

    def __init__(
        self,
        name,
        ann=None,
        features=None,
        replace=False,  # replace existing features rather than updating
        resultidx=0,
        matchidx=0,
        silent_fail=False,
    ):
        """
        Create an UpdateAnnFeatures action.

        Args:
            name: the name of the match to use for getting the annotation span
            ann: if specified use the features from this annotation. This can be either a literal annotation
                or a GetAnn helper to access another annotation from the result.
            features: the features to use for updating, either literal  features or a GetFeatures helper.
            replace: if True, replace the existing features with the new ones, otherwise update the existing features.
            resultidx: the index of the result to use, if there is more than one
            matchidx: the index of a matching info element to use, if more than one matches the given name
            silent_fail: if True, do not raise an exception if the features cannot be updated
        """
        # span is either a span, the index of a match info to take the span from, or a callable that will return the
        # span at firing time
        assert isinstance(ann, GetAnn)
        assert features is not None
        self.name = name
        self.ann = ann
        self.replace = replace
        self.features = features
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
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
        if isinstance(self.ann, Annotation):
            feats = deepcopy(self.ann.features)
        else:
            ann = self.ann(succ)
            if ann is None:
                if self.silent_fail:
                    return
                else:
                    raise Exception("No matching annotation found")
            feats = deepcopy(ann.features)
        if not feats and callable(self.features):
            feats = self.features(succ, context=context, location=location)
        elif not feats:
            feats = deepcopy(self.features)
        if self.replace:
            theann.features.clear()
        theann.features.update(feats)


# class RemoveAnn:
#     def __init__(self, name, ann=None, annset=None, resultidx=0, matchidx=0, which="first", silent_fail=True):
#         pass
#
#     def __call__(self, succ, context=None, location=None):
#         pass
#

# GETTERS


class GetAnn:
    """
    Helper to access an annoation from a match with the given name.
    """

    def __init__(self, name, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetAnn helper.

        Args:
            name: the name of the match to use.
            resultidx:  the index of the result to use if there is more than one.
            matchidx:  the index of the match info element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None.
        """
        self.name = name
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        match = _get_match(
            succ, self.name, self.resultidx, self.matchidx, self.silent_fail
        )
        ann = match.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.matchidx}"
                )
        return ann


class GetFeatures:
    """
    Helper to access the features of an annotation in a match with the given name.
    """

    def __init__(self, name, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetFeatures helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            matchidx:  the index of the match info element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        match = _get_match(
            succ, self.name, self.resultidx, self.matchidx, self.silent_fail
        )
        ann = match.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.matchidx}"
                )
        return ann.features


class GetType:
    """
    Helper to access the type of an annotation in a match with the given name.
    """

    def __init__(self, name, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetType helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            matchidx:  the index of the match info element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        match = _get_match(
            succ, self.name, self.resultidx, self.matchidx, self.silent_fail
        )
        ann = match.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.matchidx}"
                )
        return ann.type


class GetStart:
    """
    Helper to access the start offset of the annotation in a match with the given name.
    """

    def __init__(self, name, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetStart helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            matchidx:  the index of the match info element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        match = _get_match(
            succ, self.name, self.resultidx, self.matchidx, self.silent_fail
        )
        span = match["span"]
        return span.start


class GetEnd:
    """
    Helper to access the end offset of the annotation in a match with the given name.
    """

    def __init__(self, name, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetEnd helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            matchidx:  the index of the match info element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        return _get_match(
            succ, self.name, self.resultidx, self.matchidx, self.silent_fail
        )["span"].end


class GetFeature:
    """
    Helper to access the features of the annotation in a match with the given name.
    """

    def __init__(self, name, featurename, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetFeatures helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            matchidx:  the index of the match info element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail
        self.featurename = featurename

    def __call__(self, succ, context=None, location=None):
        match = _get_match(
            succ, self.name, self.resultidx, self.matchidx, self.silent_fail
        )
        ann = match.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.matchidx}"
                )
        return ann.features.get(self.featurename)


class GetText:
    """
    Helper to access text, either covered document text of the annotation or matched text.
    """

    def __init__(self, name, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetText helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            matchidx:  the index of the match info element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        match = _get_match(
            succ, self.name, self.resultidx, self.matchidx, self.silent_fail
        )
        span = match.get("span")
        if span:
            return context.doc[span]
        else:
            if self.silent_fail:
                return
            else:
                raise Exception("Could not find a span for match info")


class GetRegexGroup:
    """
    Helper to access the given regular expression matching group in a match with the given name.
    """

    def __init__(self, name, group=0, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetText helper.

        Args:
            name: the name of the match to use.
            resultidx: the index of the result to use if there is more than one.
            matchidx:  the index of the match info element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        self.name = name
        self.resultidx = resultidx
        self.matchidx = matchidx
        self.group = group
        self.silent_fail = silent_fail

    def __call__(self, succ, context=None, location=None):
        match = _get_match(
            succ, self.name, self.resultidx, self.matchidx, self.silent_fail
        )
        groups = match.get("groups")
        if groups:
            return groups[self.group]
        else:
            if self.silent_fail:
                return
            else:
                raise Exception("Could not find regexp groups for match info")
