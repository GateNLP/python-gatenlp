# TODO: currently uses intervaltree, but this is not ideal, since intervaltree does not return sorted lists
# Ideally, if we create an immutable subset of annotations, that subset should get a partial interval tree
# for those annotations, if we already have the interval tree for the original set (which in most cases we have
# since we need it for creating the subset in the first place). Then, if the intervaltree would allow ordered
# lists, we could directly use it to get the annotations in document order!


from collections import defaultdict
from intervaltree import IntervalTree, Interval
from sortedcontainers import SortedSet
from .annotation import Annotation
from .exceptions import InvalidOffsetException
import numbers


def support_annotation_or_set(method):
    """
    Decorator to allow a method that normally takes a start and end
    offset to take an annotation or annotation set or a pair of offsets instead.
    It also allows to take a single offset instead which will then be used as both start and end offset.
    """

    def _support_annotation_or_set(self, *args):
        if len(args) == 1:
            if isinstance(args[0], Annotation):
                left, right = args[0].start, args[0].end
            elif isinstance(args[0], AnnotationSet):
                left, right = args[0].span()
            elif isinstance(args[0], (tuple, list)) and len(args[0]) == 2:
                left, right = args[0]
            elif isinstance(args[0], numbers.Integral):
                left, right = args[0], args[0]
            else:
                raise Exception("Not an annotation or an annotation set or pair: {}".format(args[0]))
        else:
            assert len(args) == 2
            left, right = args

        return method(self, left, right)

    return _support_annotation_or_set


class AnnotationSet:
    def __init__(self, name="", changelog=None, owner_doc=None):
        """
        Create a new annotation set.
        :param name: the name of the annotation set. This is only really needed if the changelog is used.
        :param changelog:
        :param owner_doc:
        """
        self.changelog = changelog
        self.name = name
        self.owner_doc = owner_doc

        # NOTE: the index is only created when we actually need it!
        self._index_by_offset = None
        self._index_by_type = None
        # internally we represent the annotations as a map from annotation id (int) to Annotation
        self._annotations = {}
        self._is_immutable = False
        self._max_annid = 0

    def restrict(self, restrict_to=None):
        """
        Create an immutable copy of this set, optionally restricted to the given annotation ids.
        :param restrict_to: an iterable of annotation ids
        :return: an immutable annotation set with all the annotations of this set or restricted to the ids
        in restrict_to
        """
        annset = AnnotationSet(name="", owner_doc=self.owner_doc)
        annset._is_immutable = True
        annset._annotations = {annid: self._annotations[annid] for annid in restrict_to}
        annset._max_annid = self._max_annid
        return annset

    def _create_index_by_offset(self):
        """
        Generates the offset index, if it does not already exist.
        The offset index is an interval tree that stores the annotation ids for the offset interval of the annotation.
        """
        if self._index_by_offset is None:
            self._index_by_offset = IntervalTree()
            self._sorted_by_offset = SortedSet()
            for ann in self._annotations.values():
                self._index_by_offset[ann.start:ann.end] = ann.id
                self._sorted_by_offset.add(Interval(ann.start, ann.end, ann.id))

    def _create_index_by_type(self):
        """
        Generates the type index, if it does not already exist. The type index is a map from
        annotation type to a set of all annotation ids with that type.
        """
        if self._index_by_type is None:
            self._index_by_type = defaultdict(set)
            for ann in self._annotations.values():
                self._index_by_type[ann.type].add(ann.id)

    def _add_to_indices(self, annotation):
        """
        If we have created the indices, add the annotation to them.
        :param annotation:
        :return:
        """
        if self._index_by_type is not None:
            self._index_by_type[annotation.type].add(annotation.id)
        if self._index_by_offset is not None:
            self._index_by_offset[annotation.start:annotation.end] = annotation.id
            self._sorted_by_offset.add(Interval(annotation.start, annotation.end, annotation.id))

    def _remove_from_indices(self, annotation):
        if self._index_by_offset is not None:
            self._index_by_offset.remove(annotation.start, annotation.end, annotation.id)
        if self._index_by_type is not None:
            self._index_by_type[annotation.type].remove(annotation.id)

    @staticmethod
    def _intvs2idlist(intvs):
        """
        Convert an iterable of intervals+id to a list of ids
        :param intvs:
        :return:
        """
        return [i.data for i in intvs]

    @staticmethod
    def _intvs2idset(intvs):
        ret = set()
        for i in intvs:
            ret.add(i.data)
        return ret

    def _restrict_intvs(self, intvs):
        return self.restrict(AnnotationSet._intvs2idlist(intvs))

    def __len__(self):
        return len(self._annotations)

    def size(self):
        return len(self._annotations)

    @support_annotation_or_set
    def _check_offsets(self, start, end):
        """
        Checks the offsets for the given annotation against the document boundaries, if we know the owning
        document.
        """
        if self.owner_doc is None:
            return
        doc_size = self.owner_doc.size()

        if start < 0:
            raise InvalidOffsetException("Annotation starts before 0")
        if end < 0:
            raise InvalidOffsetException("Annotation ends before 0")
        if start > end:
            raise InvalidOffsetException("Annotation ends before it starts")
        if start > doc_size:
            raise InvalidOffsetException(
                "Annotation starts after document ends: start={}, docsize={}".format(start, doc_size))
        if end > doc_size:
            raise InvalidOffsetException(
                "Annotation ends after document ends: end={}, docsize={}".format(end, doc_size))

    def add(self, start, end, anntype, features, annid=None):
        """

        :param start: start offset
        :param end: end offset
        :param anntype: the annotation type
        :param features: a map, an iterable of tuples or an existing feature map. In any case, the features are
        used to create a new feature map for this annotation.
        :param annid: the annotation id, if not specified the next free one for this set is used
        :return:
        """
        if self._is_immutable:
            raise Exception("Cannot add an annotation to an immutable annotation set")
        self._check_offsets(start, end)
        if annid and annid in self._annotations:
            raise Exception("Cannot add annotation with id {}, already in set".format(annid))
        if annid is None:
            self._max_annid = self._max_annid + 1
            annid = self._max_annid
        ann = Annotation(start, end, anntype, annid, owner_setname=self.name,
                         changelog=self.changelog, features=features)
        self._annotations[annid] = ann
        self._add_to_indices(ann)
        if self.changelog:
            self.changelog.append({
                "command": "ADD_ANNOT",
                "set": self.name,
                "start": ann.start,
                "end": ann.end,
                "type": ann.type,
                "features": ann.features,
                "id": ann.id})
        return ann.id

    def remove(self, annotation):
        """
        Remove the given annotation which is either the id or the annotation instance.
        :param annotation: either the id (int) or the annotation instance (Annotation)
        :return:
        """
        annid = None  # make pycharm happy
        if self._is_immutable:
            raise Exception("Cannot remove an annotation from an immutable annotation set")
        if isinstance(annotation, int):
            annid = annotation
            if annid not in self._annotations:
                raise Exception("Annotation with id {} not in annotation set, cannot remove".format(annid))
            annotation = self._annotations[annid]
        elif isinstance(annotation, Annotation):
            annid = annotation.id
            if annid not in self._annotations:
                raise Exception("Annotation with id {} does not belong to this set, cannot remove".format(annid))
        del self._annotations[annid]
        if self.changelog:
            self.changelog.append({
                "command": "REMOVE_ANNOT",
                "set": self.name,
                "id": annid})

        self._remove_from_indices(annotation)

    def __iter__(self):
        """
        Iterator for going through all the annotations in arbitrary order.
        :return:
        """
        return iter(self._annotations.values())

    def in_document_order(self, *annotations, from_offset=None, to_offset=None, reverse=False, anntype=None):
        """
        Returns an iterator for going through annotations in document order. If an iterator of annotations
        is given, then those annotations, optionally limited by the other parameters are returned in
        document order, otherwise, all annotations in the set are returned, otionally limited by the other
        parameters.
        :param *annotations: either missing or exactly one parameter which must be an iterable of annotations
        from this annotation set.
        :param from_offset: the offset from where to start including annotations
        :param to_offset: the last offset to use as the starting offset of an annotation
        :param anntype: only annotations of this type
        :param reverse: process in reverse document order
        :return: iterator for annotations in document order
        """
        if from_offset is not None:
            assert from_offset >= 0
        if to_offset is not None:
            assert to_offset >= 1
        if to_offset is not None and from_offset is not None:
            assert to_offset > from_offset
        if len(annotations) == 0:
            self._create_index_by_offset()
            if from_offset is not None:
                from_offset = Interval(from_offset, 0, None)
            if to_offset is not None:
                to_offset = Interval(to_offset, 9999999999, None)  # provide a bogus end offset for sorting
            for interval in self._sorted_by_offset.irange(minimum=from_offset, maximum=to_offset, reverse=reverse):
                if anntype is not None and self._annotations[interval.data].type != anntype:
                    continue
                yield self._annotations[interval.data]
        elif len(annotations) == 1:
            for ann in sorted(annotations, reverse=reverse, key=lambda x: (x.start, x.end)):
                if anntype is not None and ann.type != anntype:
                    continue
                if from_offset is not None and ann.start < from_offset:
                    continue
                if to_offset is not None and ann.start > to_offset:
                    continue
                yield ann

    def get(self, annid, default=None):
        """
        Gets the annotation with the given annotation id or returns the given default.
        """
        return self._annotations.get(annid, default)

    # All the following methods return an immutable annotation set!

    def all_by_type(self, anntype=None):
        """
        Gets annotations of the specified type. If the anntype is None, return all annotation in an immutable set.
        Creates the type index if necessary.
        """
        self._create_index_by_type()
        if anntype is None:
            annids = self._annotations.keys()
        else:
            annids = self._index_by_type.get(anntype, None)
            if annids is None:
                annids = []
        return self.restrict(annids)

    def type_names(self):
        """
        Gets the names of all types in this set. Creates the type index if necessary.
        """
        self._create_index_by_type()
        return self._index_by_type.keys()

    def types(self):
        """
        Returns the index of types, mapping each type to the set of annotation ids of that type. If necessary
        creates the index.
        """
        self._create_index_by_type()
        return self._index_by_type

    def at(self, start):
        """
        Gets all annotations at the given offset (empty if none) and returns them in an immutable annotation set.
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset[start]
        return self._restrict_intvs(intvs)

    def first_from(self, offset):
        """
        Gets all annotations at the first valid position at or after the given offset and returns them in an immutable
        annotation set.
        """
        self._create_index_by_offset()
        intvs = sorted(self._index_by_offset[offset:])
        # now select only those first ones which all have the same offset
        if len(intvs) < 2:
            return self._restrict_intvs(intvs)
        else:
            retids = set()
            start = intvs[0].start
            for intv in intvs:
                if intv.start == start:
                    retids.add(intv.data)
            return self.restrict(retids)

    @support_annotation_or_set
    def overlapping(self, start, end):
        """
        Gets annotations overlapping with the given span.
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.overlap(start, end)
        return self._restrict_intvs(intvs)

    @support_annotation_or_set
    def covering(self, start, end):
        """
        Get the annotations which contain the given offset range (or annotation/annotation set)
        :param start: the start offset of the span
        :param end: the end offset of the span
        :return: an immutable annotation set with the matching annotations, if any
        """
        # This is not directly supported so we find the overlapping ones and then filter those where the
        # start and end fits
        # This may not be optimal
        self._create_index_by_offset()
        intvs = self._index_by_offset.overlap(start, end)
        retintvs = set()
        for intv in intvs:
            if intv.start <= start and intv.end >= end:
                retintvs.add(intv)
        return self._restrict_intvs(intvs)

    @support_annotation_or_set
    def within(self, start, end):
        """Gets annotations that fall completely within the left and right given"""
        if start == end:
            intvs = []
        elif start > end:
            raise Exception("Invalid offset range: {},{}".format(start, end))
        else:
            self._create_index_by_offset()
            intvs = self._index_by_offset.envelop(start, end)
        return self._restrict_intvs(intvs)

    @support_annotation_or_set
    def after(self, start, end=None):
        """
        Return the annotations that start after the given offset (or annotation). If an end offset or an annotation
        or an annotation set is given the end offset or end of the annotation/set is used.
        :param start: Start offset
        :param end: ignored, only here so the @support_annotation decorator works.
        :return: an immutable annotation set of the matching annotations
        """
        if end is not None:
            off = end
        else:
            off = start
        self._create_index_by_offset()
        intvs = self._index_by_offset[off:]
        return self._restrict_intvs(intvs)

    @support_annotation_or_set
    def before(self, start, end=None):
        """
        Return the annotations that start before the given offset (or annotation). This also accepts an annotation
        or set.
        :param start: Start offset
        :param end: ignored, only here so the @support_annotation decorator works.
        :return: an immutable annotation set of the matching annotations
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset[0:start]
        return self._restrict_intvs(intvs)

    def first(self, by_end=False):
        """
        Return the/an annotation that has the smallest start offset (and shortest length if several such).
        If by_end is True, instead return the/an annotation that has the smallest end offset.
        :return: the annotation, or None if the annotation set is empty
        """
        if len(self._annotations) == 0:
            return None
        elif len(self._annotations) == 1:
            return next(iter(self._annotations.values()))
        if by_end:
            min_end = 999999999999
            min_ann = None
            for ann in self:
                if ann.end < min_end:
                    min_end = ann.end
                    min_ann = ann
            return min_ann
        else:
            self._create_index_by_offset()
            return self._annotations[self._sorted_by_offset[0].data]

    def last(self, by_end=False):
        """
        Gets the/an annotation with the biggest start offset (and longest length if several such).
        :return: the annotation, or None if the annotation set is empty
        """
        if len(self._annotations) == 0:
            return None
        elif len(self._annotations) == 1:
            return next(iter(self._annotations.values()))
        if by_end:
            max_end = -1
            max_ann = None
            for ann in self:
                if ann.end > max_end:
                    max_end = ann.end
                    max_ann = ann
            return max_ann
        else:
            self._create_index_by_offset()
            return self._annotations[self._sorted_by_offset[-1].data]

    def span(self):
        """
        Returns a tuple with the start and end offset the corresponds to the smallest start offset of any annotation
        and the largest end offset of any annotation.
        (Currently requires O(n) every time it is called)
        :return: tuple of minimum start offset and maximum end offset
        """
        min_start = 99999999999
        max_end = -1
        for ann in self:
            if ann.start < min_start:
                min_start = ann.start
            if ann.end > max_end:
                max_end = ann.end
        return min_start, max_end

    def __contains__(self, annorannid):
        """Provides annotation in annotation_set functionality"""
        if isinstance(annorannid, Annotation):
            return annorannid.id in self._annotations
        return annorannid in self._annotations  # On the off chance someone passed an ID in directly

    contains = __contains__

    def __repr__(self):
        return "AnnotationSet({})".format(repr(list(self.in_document_order())))

    def json_repr(self, **kwargs):
        return {
            "annotations": [ann.json_repr(**kwargs) for ann in self._annotations.values()],
            "max_annid": self._max_annid
        }
