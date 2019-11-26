"""
A simple class that represents a collection of sorted intervals and allows for some basic interval-based
operations. Internally this stores the intervals using standard sorted lists. This is not optimal and my
incur a O(n) overhead on some operations depending on the result set. It also may incur a significant overhead
for creating and maintaning the sorted lists.
NOTE: this stores a tuple (start, end, object) in the sorted list and uses a key function that returns the offset
for sorting.
"""

from sortedcontainers import SortedKeyList


class SortedIntvls:
    def __init__(self):
        # NOTE: we sort by increasing start offset and decreasing end offset for this
        self._by_start = SortedKeyList(key=lambda x: x[0])
        # for this we only sort by the end offset
        self._by_end = SortedKeyList(key=lambda x: x[1])

    def add(self, start, end, data):
        self._by_start.add((start, end, data))
        self._by_end.add((start, end, data))

    def update(self, tupleiterable):
        self._by_start.update(tupleiterable)
        self._by_end.update(tupleiterable)

    def remove(self, start, end, data):
        self._by_start.remove((start, end, data))
        self._by_end.remove((start, end, data))

    def discard(self, start, end, data):
        self._by_start.discard((start, end, data))
        self._by_end.discard((start, end, data))

    def __len__(self):
        return len(self._by_start)

    def starting_at(self, offset):
        """
        Return an iterable of (start, end, data) tuples where start==offset
        :param offset: the starting offset
        :return:
        """
        return self._by_start.irange_key(min_key=offset, max_key=offset)

    def ending_at(self, offset):
        """
        Return an iterable of (start, end, data) tuples where end==offset
        :param offset: the ending offset
        :return:
        """
        return self._by_end.irange_key(min_key=offset, max_key=offset)

    def at(self, start, end):
        """
        Return iterable of tuples where start==start and end==end
        :param start:
        :param end:
        :return:
        """
        for intvl in self._by_start.irange_key(min_key=start, max_key=start):
            if intvl[1] == end:
                yield intvl

    # SAME as within
    def within(self, start, end):
        """
        Return intervals which are fully contained within start...end
        :param start:
        :param end:
        :return:
        """
        # get all the intervals that start within the range, then keep those which also end within the range
        for intvl in self._by_start.irange_key(min_key=start, max_key=end):
            if intvl[1] <= end:
                yield intvl

    def starting_from(self, offset):
        """
        Intervals that start at or after offset.
        :param offset:
        :return:
        """
        return self._by_start.irange_key(min_key=offset)

    def starting_before(self, offset):
        """
        Intervals that start before offset
        :param offset:
        :return:
        """
        return self._by_start.irange_key(max_key=offset-1)


    def ending_to(self, offset):
        """
        Intervals that end before or at the given end offset.
        NOTE: the result is sorted by end offset, not start offset!
        :param offset:
        :return:
        """
        return self._by_end.irange_key(max_key=offset)

    def ending_after(self, offset):
        """
        Intervals the end after the given offset
        NOTE: the result is sorted by end offset!
        :param offset:
        :return:
        """
        return self._by_end.irange_key(min_key=offset+1)

    # SAME as covering
    def covering(self, start, end):
        """
        Intervals that contain the given range
        :param start:
        :param end:
        :return:
        """
        # All intervals that start at or before the start and end at or after the end offset
        # we do this by first getting the intervals the start before or atthe start
        # then filtering by end
        for intvl in self._by_start.irange_key(max_key=start):
            if intvl[1] >= end:
                yield intvl

    def overlapping(self, start, end):
        """
        Intervals that overlap with the given range.
        :param start:
        :param end:
        :return:
        """
        # All intervals where the start offset is before the end and the end offset is after the start
        # plus all intervals where the start offset is after the start but before the end
        # and the end offset is after the end
        for intvl in self._by_start.irange_key(max_key=end-1):
            if intvl[1] > start+1:
                yield intvl

    def firsts(self):
        """
        Return an iterator of all intervals at the minimum start offset that exists.
        :return:
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
        Return an iterator of all intervals at the maximum start offset that exists.
        :return:
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
        Returns the smallest start offset we have
        :return:
        """
        return self._by_start[0][0]

    def max_end(self):
        """
        Returns the biggest end offset we have
        :return:
        """
        return self._by_end[-1][1]

    def irange(self, minoff=None, maxoff=None, reverse=False):
        return self._by_start.irange_key(min_key=minoff, max_key=maxoff, reverse=reverse)

    def __repr__(self):
        return "SortedIntvls({},{})".format(self._by_start, self._by_end)
