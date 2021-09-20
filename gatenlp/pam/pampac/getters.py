"""
Module for PAMPAC getter helper classes
"""

from gatenlp.pam.pampac.actions import Getter


class GetAnn(Getter):
    """
    Helper to access an annoation from a match with the given name.
    """

    def __init__(self, name, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetAnn helper.

        Args:
            name: the name of the match to use.
            resultidx:  the index of the result to use if there is more than one, if None, use the one(s)
                processed by the action.
            matchidx:  the index of the match info element with the given name to use if there is more than one, if
                None, use the one processed by the action
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None.
        """
        super().__init__(name=name, resultidx=resultidx, matchidx=matchidx, silent_fail=silent_fail)

    def __call__(self, succ, context=None, location=None, resultidx=None, matchidx=None):
        """
        This is how the getter should get invoked by the action. If resultidx/matchidx is not None,
        then we use these if our own init parms for these were None.

        Args:
            succ: succes object
            context: context object
            location: location object
            resultidx: resultindex getting processed by the action
            matchidx: match index getting processed by the action

        Returns:
            Something related to the match
        """
        match = self._get_match(
            succ, resultidx, matchidx
        )
        ann = match.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.matchidx}"
                )
        return ann


class GetFeatures(Getter):
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
        super().__init__(name=name, resultidx=resultidx, matchidx=matchidx, silent_fail=silent_fail)

    def __call__(self, succ, context=None, location=None, resultidx=None, matchidx=None):
        match = self._get_match(
            succ, resultidx, matchidx
        )
        ann = match.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.matchidx}"
                )
        return ann.features


class GetType(Getter):
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
        super().__init__(name=name, resultidx=resultidx, matchidx=matchidx, silent_fail=silent_fail)

    def __call__(self, succ, context=None, location=None, resultidx=None, matchidx=None):
        match = self._get_match(
            succ, resultidx, matchidx
        )
        ann = match.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.matchidx}"
                )
        return ann.type


class GetStart(Getter):
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
        super().__init__(name=name, resultidx=resultidx, matchidx=matchidx, silent_fail=silent_fail)

    def __call__(self, succ, context=None, location=None, resultidx=None, matchidx=None):
        match = self._get_match(
            succ, resultidx, matchidx
        )
        span = match["span"]
        return span.start


class GetEnd(Getter):
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
        super().__init__(name=name, resultidx=resultidx, matchidx=matchidx, silent_fail=silent_fail)

    def __call__(self, succ, context=None, location=None, resultidx=None, matchidx=None):
        return self._get_match(
            succ, resultidx, matchidx
        )["span"].end


class GetFeature(Getter):
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
        super().__init__(name=name, resultidx=resultidx, matchidx=matchidx, silent_fail=silent_fail)
        self.featurename = featurename

    def __call__(self, succ, context=None, location=None, resultidx=None, matchidx=None):
        match = self._get_match(
            succ, resultidx, matchidx
        )
        ann = match.get("ann")
        if ann is None:
            if not self.silent_fail:
                raise Exception(
                    f"No annotation found for name {self.name}, {self.resultidx}, {self.matchidx}"
                )
        return ann.features.get(self.featurename)


class GetText(Getter):
    """
    Helper to access text, either covered document text of the annotation or matched text.
    """

    def __init__(self, name=None, resultidx=0, matchidx=0, silent_fail=False):
        """
        Create a GetText helper. This first gets the span that matches the name, resultidx and matchidx
        parameters and then provides the text of the document for that span.

        Args:
            name: the name of the match to use, if None, use the span of the whole match.
            resultidx: the index of the result to use if there is more than one.
            matchidx:  the index of the match info element with the given name to use if there is more than one
            silent_fail: if True, do not raise an exception if the annotation cannot be found, instead return
                None
        """
        super().__init__(name=name, resultidx=resultidx, matchidx=matchidx, silent_fail=silent_fail)

    def __call__(self, succ, context=None, location=None, resultidx=None, matchidx=None):
        if self.name is None:
            span = self._get_span(succ, resultidx, matchidx)
        else:
            match = self._get_match(succ, resultidx, matchidx)
            span = match.get("span")
        if span:
            return context.doc[span]
        else:
            if self.silent_fail:
                return None
            else:
                raise Exception("Could not find a span for match info")


class GetRegexGroup(Getter):
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
        super().__init__(name=name, resultidx=resultidx, matchidx=matchidx, silent_fail=silent_fail)

    def __call__(self, succ, context=None, location=None, resultidx=None, matchidx=None):
        match = self._get_match(
            succ, resultidx, matchidx
        )
        groups = match.get("groups")
        if groups:
            return groups[self.group]
        else:
            if self.silent_fail:
                return None
            else:
                raise Exception("Could not find regexp groups for match info")
