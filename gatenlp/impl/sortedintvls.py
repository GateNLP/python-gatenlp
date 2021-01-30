"""
Module that provides a simple class that represents a collection of sorted intervals and allows for some
basic interval-based operations.

Internally this stores the intervals using standard sorted lists. This is not optimal and may
incur a O(n) overhead on some operations depending on the result set. It also may incur a significant overhead
for creating and maintaning the sorted lists.

NOTE: this stores a tuple (start, end, annid, object) in the sorted lists for the start  and end offsets
and uses a key function that returns which elements to use for sorting.

For the list sorted by start offset, we use the start offset and annotation id. For the end offset we use the
end offset of the annotation only.
"""

import sys
from sortedcontainers import SortedKeyList


class SortedIntvls:
    """ """

    def __init__(self, by_ol=False):
        """
        Create an interval index. By default, this sorts by start offset and
        annotation id. If by_ol is True, sorts by start offset, end offset and annotation id.

        Args:
            by_ol: if True, use start offset, end offset, annotation id
        """
        if by_ol:
            # we sort by increasing start offset then increasing annotation id for this
            self._by_start = SortedKeyList(key=lambda x: (x[0], x[1], x[2]))
        else:
            # we sort by increasing start offset then increasing annotation id for this
            self._by_start = SortedKeyList(key=lambda x: (x[0], x[2]))
        # for this we sort by end offset only
        self._by_end = SortedKeyList(key=lambda x: x[1])

    def add(self, start, end, data):
        """
        Adds an interval.
        """
        self._by_start.add((start, end, data))
        self._by_end.add((start, end, data))

    def update(self, tupleiterable):
        """
        Updates from an iterable of intervals.
        """
        self._by_start.update(tupleiterable)
        self._by_end.update(tupleiterable)

    def remove(self, start, end, data):
        """
        Removes an interval, exception if the interval does not exist.
        """
        self._by_start.remove((start, end, data))
        self._by_end.remove((start, end, data))

    def discard(self, start, end, data):
        """
        Removes and interval, do nothing if the interval does not exist.
        """
        self._by_start.discard((start, end, data))
        self._by_end.discard((start, end, data))

    def __len__(self):
        """
        Returns the number of intervals.
        """
        return len(self._by_start)

    def starting_at(self, offset):
        """
        Returns an iterable of (start, end, data) tuples where start==offset
        """
        return self._by_start.irange_key(
            min_key=(offset, 0), max_key=(offset, sys.maxsize)
        )

    def ending_at(self, offset):
        """
        Returns an iterable of (start, end, data) tuples where end==offset
        """
        return self._by_end.irange_key(min_key=offset, max_key=offset)

    def at(self, start, end):
        """
        Returns an iterable of tuples where start==start and end==end
        """
        for intvl in self._by_start.irange_key(
            min_key=(start, 0), max_key=(start, sys.maxsize)
        ):
            if intvl[1] == end:
                yield intvl

    def within(self, start, end):
        """
        Returns intervals which are fully contained within start...end
        """
        # get all the intervals that start within the range, then keep those which also end within the range
        for intvl in self._by_start.irange_key(
            min_key=(start, 0), max_key=(end, sys.maxsize)
        ):
            if intvl[1] <= end:
                yield intvl

    def starting_from(self, offset):
        """
        Returns intervals that start at or after offset.
        """
        return self._by_start.irange_key(min_key=(offset, 0))

    def starting_before(self, offset):
        """
        Returns intervals  that start before offset.
        """
        return self._by_start.irange_key(max_key=(offset - 1, sys.maxsize))

    def ending_to(self, offset):
        """
        Returns intervals that end before or at the given end offset.
        """
        return self._by_end.irange_key(max_key=offset)

    def ending_after(self, offset):
        """
        Returns intervals the end after the given offset.
        """
        return self._by_end.irange_key(min_key=offset + 1)

    def covering(self, start, end):
        """
        Returns intervals that contain the given range.
        """
        # All intervals that start at or before the start and end at or after the end offset
        # we do this by first getting the intervals the start before or at the start
        # then filtering by end
        # NOTE: if the given range is zero length, then if the interval starts before the start
        # it must end at least 1 after the end!
        if start == end:
            for intvl in self._by_start.irange_key(max_key=(start, sys.maxsize)):
                if intvl[0] < start and intvl[1] > end:
                    yield intvl
                elif intvl[0] == start and intvl[1] >= end:
                    yield intvl
        else:
            for intvl in self._by_start.irange_key(max_key=(start, sys.maxsize)):
                if intvl[1] >= end:
                    yield intvl

    def overlapping(self, start, end):
        """
        Returns intervals that overlap with the given range.
        """
        # All intervals where the start or end offset lies within the given range.
        # This excludes the ones where the end offset is before the start or
        # where the start offset is after the end of the range.
        # Here we do this by looking at all intervals where the start offset is before the
        # end of the range. This still includes those which also end before the start of the range
        # so we check in addition that the end is larger than the start of the range.
        # NOTE: if the given range has zero length, then any annotation that starts before or at start
        # AND ends at or after start==end is overlapping
        if start == end:
            # in order to check what is overlapping with the zero length span, we need to find
            # intervals which start before the start of that span AND end at least one after that span;
            # or intervals which start at the span and end with the span or after.
            # In other words we look at all intervals which start anywhere before or at the start(=end)
            # of the span.
            # if the start of what we found is < start then end must be > start, otherwise (if starts are same)
            # end must be >= start
            for intvl in self._by_start.irange_key(max_key=(end, sys.maxsize)):
                if intvl[0] < start and intvl[1] > start:
                    yield intvl
                elif intvl[0] == start and intvl[1] >= start:
                    yield intvl
        else:
            for intvl in self._by_start.irange_key(max_key=(end - 1, sys.maxsize)):
                if intvl[0] == intvl[1]:  # we need to check a zero length interval
                    if intvl[0] >= start:
                        yield intvl
                else:
                    if intvl[1] > start + 1:
                        yield intvl

    def firsts(self):
        """
        Yields all intervals which start at the smallest known offset.
        """
        laststart = None
        # logger.info("DEBUG: set laststart to None")
        for intvl in self._by_start.irange_key():
            # logger.info("DEBUG: checking interval {}".format(intvl))
            if laststart is None:
                laststart = intvl[0]
                # logger.info("DEBUG: setting laststart to {} and yielding {}".format(intvl[0], intvl))
                yield intvl
            elif intvl[0] == laststart:
                # logger.info("DEBUG: yielding {}".format(intvl))
                yield intvl
            else:
                # logger.info("DEBUG: returning since we got {}".format(intvl))
                return

    def lasts(self):
        """
        Yields all intervals which start at the last known start offset.
        """
        laststart = None
        for intvl in reversed(self._by_start):
            if laststart is None:
                laststart = intvl[0]
                yield intvl
            elif intvl[0] == laststart:
                yield intvl
            else:
                return

    def min_start(self):
        """
        Returns the smallest known start offset.
        """
        return self._by_start[0][0]

    def max_end(self):
        """
        Returns the biggest known end offset.
        """
        return self._by_end[-1][1]

    def irange(self, minoff=None, maxoff=None, reverse=False, inclusive=(True, True)):
        """
        Yields an iterator of intervals with a start offset between minoff and maxoff, inclusive.

        Args:
          minoff: minimum offset, default None indicates any
          maxoff: maximum offset, default None indicates any
          reverse: if `True` yield in reverse order
          inclusive: if the minoff and maxoff values should be inclusive, default is (True,True)

        Returns:

        """
        return self._by_start.irange_key(
            min_key=minoff, max_key=maxoff, reverse=reverse, inclusive=inclusive
        )

    def __repr__(self):
        return "SortedIntvls({},{})".format(self._by_start, self._by_end)
