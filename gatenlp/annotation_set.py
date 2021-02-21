"""
Module for AnnotationSet class which represents a named collection of
annotations which can arbitrarily overlap.
"""

# TODO: when should two sets be equal? Currently object identity is requried!

from typing import Any, List, Union, Dict, Set, KeysView, Iterator, Generator
from collections.abc import Iterable
from collections import defaultdict
import copy
from gatenlp.span import Span
from gatenlp.annotation import Annotation
from gatenlp.impl import SortedIntvls
from gatenlp.utils import support_annotation_or_set, allowspan

__pdoc__ = {
    "AnnotationSet.__iter__": True,
    "AnnotationSet.__contains__": True,
    "AnnotationSet.__getitem__": True,
    "AnnotationSet.__len__": True,
}


class InvalidOffsetError(KeyError):
    """ """

    pass


class AnnotationSet:
    def __init__(self, name: str = "", owner_doc=None):
        """
        Creates an annotation set. This should not be used directly by the
        user, instead the method `Document.annset(name)` should be used to
        access the annotation set with a given name from the document.

        An annotation set contains an arbitrary number of annotations, which
        can overlap in arbitrary ways. Each annotation set has a name and a
        document can have as many named annotation sets as needed.


        Args:
          name: the name of the annotation set, default: the empty string
              (default annotation set)
          owner_doc: if this is set, the set and all sets created from it
              can be queried for the owning document and offsets get checked
              against the text of the owning document, if it has text.
              Also, the changelog is only updated if an annotation
              set has an owning document.
        """
        self._name = name
        self._owner_doc = owner_doc
        self._index_by_offset = None
        self._index_by_ol = None
        self._index_by_type = None
        # internally we represent the annotations as a map from
        # annotation id (int) to Annotation
        self._annotations = {}
        self._is_immutable = False
        self._next_annid = 0

    @property
    def name(self):
        """
        Returns the name of the annotation set.

        Note: the name of a set cannot be changed.
        """
        return self._name

    @property
    def changelog(self):
        """
        Returns the changelog or None if no changelog is set.
        """
        if self._owner_doc is None:
            return None
        return self._owner_doc.changelog

    def __setattr__(self, key, value):
        """
        Prevent immutable fields from getting overridden, once they have been
        set.
        """
        if key == "name" or key == "owner_doc":
            if self.__dict__.get(key, None) is None:
                super().__setattr__(key, value)
            else:
                raise Exception(
                    "AnnotationSet attribute cannot get changed after being set"
                )
        else:
            super().__setattr__(key, value)

    def detach(self, restrict_to=None):
        """
        Creates an immutable and detached copy of this set, optionally
        restricted to the given annotation ids. A detached annotation
        set does not have an owning document and deleting or adding
        annotations does not change the annotations stored with the document.
        However, the annotations in a detached annotation set
        are the same as those stored in the attached set, so updating their
        features will modify the annotations in the document as well.

        Args:
          restrict_to: an iterable of annotation ids, if None, all the
              annotations from this set.

        Returns:
          an immutable annotation set
        """
        annset = AnnotationSet(name="detached-from:" + self.name)
        annset._is_immutable = True
        if restrict_to is None:
            annset._annotations = {
                annid: self._annotations[annid] for annid in self._annotations.keys()
            }
        else:
            annset._annotations = {
                annid: self._annotations[annid] for annid in restrict_to
            }
        annset._next_annid = self._next_annid
        return annset

    def detach_from(self, anns: Iterable):
        """
        Creates an immutable detached annotation set from the annotations
        in anns which could by either a collection of annotations or
        annotation ids (int numbers) which are assumed to be the annotation
        ids from this set.

        The next annotation id for the created set is the highest seen
        annotation id from anns plus one.

        Args:
          anns: an iterable of annotations

        Returns:
          an immutable detached annotation set
        """
        annset = AnnotationSet(name="detached-from:" + self.name)
        annset._is_immutable = True
        annset._annotations = {}
        nextid = -1
        for ann in anns:
            if isinstance(ann, int):
                annset._annotations[ann] = self._annotations[ann]
                annid = ann
            else:
                annset._annotations[id] = ann
                annid = ann.id
            if annid > nextid:
                nextid = annid
        annset._next_annid = nextid + 1
        return annset

    @property
    def immutable(self) -> bool:
        """
        Get or set the immutability of the annotation set. If it is
        immutable, annotations cannot be added or removed from the set,
        but the annotations themselves can still have their features modified.

        All detached annotation sets are immutable when created,
        but can be made mutable afterwards.
        """
        return self._is_immutable

    @immutable.setter
    def immutable(self, val: bool) -> None:
        self._is_immutable = val

    def isdetached(self) -> bool:
        """
        Returns True if the annotation set is detached, False otherwise.
        """
        return self._owner_doc is None

    def _create_index_by_offset(self) -> None:
        """
        Generates the offset index, if it does not already exist.
        The offset index is an interval tree that stores the annotation
        ids for the offset interval of the annotation.
        """
        if self._index_by_offset is None:
            self._index_by_offset = SortedIntvls()
            for ann in self._annotations.values():
                self._index_by_offset.add(ann.start, ann.end, ann.id)

    def _create_index_by_ol(self) -> None:
        """
        Generates an index by start offset, end offset and annotation id
        """
        if self._index_by_ol is None:
            self._index_by_ol = SortedIntvls(by_ol=True)
            for ann in self._annotations.values():
                self._index_by_ol.add(ann.start, ann.end, ann.id)

    def _create_index_by_type(self) -> None:
        """
        Generates the type index, if it does not already exist.
        The type index is a map from
        annotation type to a set of all annotation ids with that type.
        """
        if self._index_by_type is None:
            self._index_by_type = defaultdict(set)
            for ann in self._annotations.values():
                self._index_by_type[ann.type].add(ann.id)

    def _add_to_indices(self, annotation: Annotation) -> None:
        """
        If we have created the indices, add the annotation to them.

        Args:
          annotation: the annotation to add to the indices.
          annotation: Annotation:
        """
        if self._index_by_type is not None:
            self._index_by_type[annotation.type].add(annotation.id)
        if self._index_by_offset is not None:
            self._index_by_offset.add(annotation.start, annotation.end, annotation.id)

    def _remove_from_indices(self, annotation: Annotation) -> None:
        """
        Remove an annotation from the indices.

        Args:
          annotation: the annotation to remove.
          annotation: Annotation:
        """
        if self._index_by_offset is not None:
            self._index_by_offset.remove(
                annotation.start, annotation.end, annotation.id
            )
        if self._index_by_type is not None:
            self._index_by_type[annotation.type].remove(annotation.id)

    @staticmethod
    def _intvs2idlist(intvs, ignore=None) -> List[int]:
        """
        Convert an iterable of interval tuples (start, end, id) to a list of ids

        Args:
          intvs: iterable of interval tuples
          ignore: an optional annotation id that should not get included 
              in the result (Default value = None)

        Returns:
          list of ids
        """
        if ignore is not None:
            return [i[2] for i in intvs if i[2] != ignore]
        else:
            return [i[2] for i in intvs]

    @staticmethod
    def _intvs2idset(intvs, ignore=None) -> Set[int]:
        """
        Convert an iterable of interval tuples (start, end, id) to a
        set of ids

        Args:
            intvs: iterable of interval tuples
            ignore:  (Default value = None)

        Returns:
            set of ids
        """
        ret = set()
        if ignore is not None:
            for i in intvs:
                if i[2] != ignore:
                    ret.add(i[2])
        else:
            for i in intvs:
                ret.add(i[2])
        return ret

    def _restrict_intvs(self, intvs, ignore=None):
        """

        Args:
          intvs:
          ignore:  (Default value = None)
        """
        return self.detach(
            restrict_to=AnnotationSet._intvs2idlist(intvs, ignore=ignore)
        )

    def __len__(self) -> int:
        """
        Return number of annotations in the set.
        """
        return len(self._annotations)

    @property
    def size(self) -> int:
        """
        Returns the number of annotations in the annotation set.
        """
        return len(self._annotations)

    @property
    def document(self):
        """
        Returns the owning document, if set. If the owning document was not set, returns None.
        """
        return self._owner_doc

    @support_annotation_or_set
    def _check_offsets(self, start: int, end: int, annid=None) -> None:
        """
        Checks the offsets for the given span/annotation against the document boundaries, if we know the owning
        document and if the owning document has text.

        Args:
          start: start offset
          end: end offset
          annid:  (Default value = None)
        """
        if self._owner_doc is None:
            return
        if self._owner_doc.text is None:
            return
        doc_size = len(self._owner_doc)

        if start < 0:
            raise InvalidOffsetError("Annotation starts before 0")
        if end < 0:
            raise InvalidOffsetError("Annotation ends before 0")
        if start > end:
            raise InvalidOffsetError("Annotation ends before it starts")
        if start > doc_size:
            raise InvalidOffsetError(
                "Annotation starts after document ends: start={}, docsize={}".format(
                    start, doc_size
                )
            )
        if end > doc_size:
            raise InvalidOffsetError(
                "Annotation ends after document ends: end={}, docsize={}".format(
                    end, doc_size
                )
            )

    @property
    def start(self):
        """
        Returns the smallest start offset of all annotations, i.e the start
        of the span of the whole set. This needs the index and creates
        it if necessary.

        Throws:
            an exception if there are no annotations in the set.
        """
        if self.size == 0:
            raise Exception("Annotation set is empty, cannot determine start offset")
        self._create_index_by_offset()
        return self._index_by_offset.min_start()

    @property
    def end(self):
        """
        Returns the end offset of the annotation set, i.e. the biggest end offset of any annotation.
        This needs the index and creates it if necessary.

        Throws:
            an exception if there are no annotations in the set.
        """
        if self.size == 0:
            raise Exception("Annotation set is empty, cannot determine end offset")
        self._create_index_by_offset()
        return self._index_by_offset.max_end()

    @property
    def length(self):
        """
        Returns the the length of the annotation set span.

        Throws:
          an exception if there are no annotations in the set.
        """
        return self.end - self.start

    @allowspan
    def add(
        self,
        start: int,
        end: int,
        anntype: str,
        features: Dict[str, Any] = None,
        annid: int = None,
    ):
        """
        Adds an annotation to the set. Once an annotation has been added,
        the start and end offsets,
        the type, and the annotation id of the annotation are immutable.

        Args:
          start: start offset
          end: end offset
          anntype: the annotation type
          features: a map, an iterable of tuples or an existing feature map.
              In any case, the features are used
              to create a new feature map for this annotation. If the map
              is empty or this parameter is None, the
              annotation does not store any map at all.
          annid: the annotation id, if not specified the next free one
              for this set is used. NOTE: the id should
              normally left unspecified and get assigned automatically.

        Returns:
            the new annotation
        """
        if annid is not None and not isinstance(annid, int):
            raise Exception("Parameter annid must be an int, mixed up with features?")
        if features is not None and isinstance(features, int):
            raise Exception(
                "Parameter features must not be an int: mixed up with annid?"
            )
        if self._is_immutable:
            raise Exception("Cannot add an annotation to an immutable annotation set")
        self._check_offsets(start, end)
        if annid and annid in self._annotations:
            raise Exception(
                "Cannot add annotation with id {}, already in set".format(annid)
            )
        if annid is None:
            annid = self._next_annid
            self._next_annid = self._next_annid + 1
        ann = Annotation(start, end, anntype, features=features, annid=annid)
        ann._owner_set = self
        if not self._annotations:
            self._annotations = {}
        self._annotations[annid] = ann
        self._add_to_indices(ann)
        if self.changelog is not None:
            entry = {
                "command": "annotation:add",
                "set": self.name,
                "start": ann.start,
                "end": ann.end,
                "type": ann.type,
                "features": ann._features.to_dict(),
                "id": ann.id,
            }
            self.changelog.append(entry)
        return ann

    def add_ann(self, ann, annid: int = None):
        """
        Adds a shallow copy of the given ann to the annotation set,
        either with a new annotation id or
        with the one given.

        Args:
          ann: the annotation to copy into the set
          annid: the annotation id, if not specified the next free one for
              this set is used. Note: the id should normally left unspecified
              and get assigned automatically.

        Returns:
          the added annotation
        """
        return self.add(ann.start, ann.end, ann.type, ann.features, annid=annid)

    def remove(
        self, annoriter: Union[int, Annotation, Iterable], raise_on_notexisting=True
    ) -> None:
        """
        Removes the given annotation which is either the id or the annotation
        instance or recursively all annotations in the iterable.

        Throws:
            exception if the annotation set is immutable or the annotation
            is not in the set

        Args:
          annoriter: either the id (int) or the annotation instance
              (Annotation) or an iterable of
              id or annotation instance or iterable ...
          raise_on_notexisting: (default: True) if false, silently accepts
              non-existing annotations/ids and does nothing.
              Note: if this is True, but the annotation set is immutable,
              an Exception is still raised.
        """
        if self._is_immutable:
            raise Exception(
                "Cannot remove an annotation from an immutable annotation set"
            )
        if isinstance(annoriter, Iterable):
            for a in annoriter:
                self.remove(a, raise_on_notexisting=raise_on_notexisting)
            return
        annid = None  # make pycharm happy
        if isinstance(annoriter, int):
            annid = annoriter
            if annid not in self._annotations:
                raise Exception(
                    "Annotation with id {} not in annotation set, cannot remove".format(
                        annid
                    )
                )
            annoriter = self._annotations[annid]
        elif isinstance(annoriter, Annotation):
            annid = annoriter.id
            if annid not in self._annotations:
                raise Exception(
                    "Annotation with id {} does not belong to this set, cannot remove".format(
                        annid
                    )
                )
        # NOTE: once the annotation has been removed from the set, it could
        # still be referenced
        # somewhere else and its features could get modified. In order to
        # prevent logging of such changes,
        # the owning set gets cleared for the annotation
        annoriter._owner_set = None
        del self._annotations[annid]
        if self.changelog is not None:
            self.changelog.append(
                {"command": "annotation:remove", "set": self.name, "id": annid}
            )
        self._remove_from_indices(annoriter)

    def clear(self) -> None:
        """
        Removes all annotations from the set.
        """
        self._annotations.clear()
        self._index_by_offset = None
        self._index_by_type = None
        if self.changelog is not None:
            self.changelog.append({"command": "annotations:clear", "set": self.name})

    def clone_anns(self, memo=None):
        """
        Replaces the annotations in this set with deep copies of the
        originals. If this is a detached set,
        then this makes sure that any modifications to the annotations do not
        affect the original annotations
        in the attached set. If this is an attached set, it makes sure that
        all other detached sets cannot affect
        the annotations in this set any more. The owning set of the
        annotations that get cloned is cleared.

        Args:
            memo: for internal use by our __deepcopy__ implementation.
        """
        tmpdict = {}
        for annid, ann in self._annotations.items():
            newann = copy.deepcopy(ann, memo=memo)
            ann._owner_set = None
            tmpdict[annid] = newann
        for annid, ann in tmpdict.items():
            self._annotations[annid] = ann

    def __copy__(self):
        """
        NOTE: creating a copy always creates a detached set, but a mutable one.
        """
        c = self.detach()
        c._is_immutable = False
        return c

    def copy(self):
        """
        Returns a shallow copy of the annotation set.
        """
        return self.__copy__()

    def __deepcopy__(self, memo=None):
        if memo is None:
            memo = {}
        c = self.detach()
        c._is_immutable = False
        c.clone_anns(memo=memo)
        return c

    def deepcopy(self):
        """
        Returns a deep copy of the annotation set.
        """
        return copy.deepcopy(self)

    def __iter__(self) -> Iterator:
        """
        Yields all the annotations of the set.

        Important: using the iterator will always create the index if it
        is not already there!
        For fast iteration use fast_iter() which does not allow sorting or
        offset ranges.

        Yields:
            the annotations in document order
        """
        # return iter(self._annotations.values())
        return self.iter()

    def fast_iter(self) -> Generator:
        """
        Yields annotations in insertion order. This is faster then the
        default iterator and does not
        need to index (so if the index does not exist, it will not be built).
        """
        if self._annotations:
            for annid, ann in self._annotations.items():
                yield ann

    def iter(
        self,
        start_ge: Union[int, None] = None,
        start_lt: Union[None, int] = None,
        with_type: str = None,
        reverse: bool = False,
    ) -> Generator:
        """
        Yields annotations ordered by starting annotation and annotation id, otionally limited
        by the other parameters.

        Args:
          start_ge: the offset from where to start including annotations
          start_lt: the last offset to use as the starting offset of an annotation
          with_type: only annotations of this type
          reverse: process in reverse document order

        Yields:
          annotations in document order

        """

        if with_type is not None:
            allowedtypes = set()
            if isinstance(type, str):
                allowedtypes.add(with_type)
            else:
                for atype in with_type:
                    allowedtypes.add(atype)
        else:
            allowedtypes = None
        if not self._annotations:
            return
        maxoff = None
        if start_ge is not None:
            assert start_ge >= 0
        if start_lt is not None:
            assert start_lt >= 1
            maxoff = start_lt + 1
        if start_lt is not None and start_ge is not None:
            assert start_lt > start_ge
        self._create_index_by_offset()
        for _start, _end, annid in self._index_by_offset.irange(
            minoff=start_ge, maxoff=maxoff, reverse=reverse
        ):
            if (
                allowedtypes is not None
                and self._annotations[annid].type not in allowedtypes
            ):
                continue
            yield self._annotations[annid]

    def iter_ol(
        self,
        start_ge: Union[int, None] = None,
        start_lt: Union[None, int] = None,
        with_type: str = None,
        reverse: bool = False,
    ) -> Generator:
        """
        Yields annotations ordered by start offset, end offset and annotoation
        id, otionally limited
        by the other parameters. If two annoations start at the same offset,
        they are always
        ordered by increasing annotation id.

        Args:
            start_ge: the offset from where to start including annotations
            start_lt: the last offset to use as the starting offset of an annotation
            with_type: only annotations of this type
            reverse: process in reverse document order

        Yields:
            annotations in document order

        """

        if with_type is not None:
            allowedtypes = set()
            if isinstance(type, str):
                allowedtypes.add(with_type)
            else:
                for atype in with_type:
                    allowedtypes.add(atype)
        else:
            allowedtypes = None
        if not self._annotations:
            return
        maxoff = None
        if start_ge is not None:
            assert start_ge >= 0
        if start_lt is not None:
            assert start_lt >= 1
            maxoff = start_lt + 1
        if start_lt is not None and start_ge is not None:
            assert start_lt > start_ge
        self._create_index_by_ol()
        for _start, _end, annid in self._index_by_ol.irange(
            minoff=start_ge, maxoff=maxoff, reverse=reverse
        ):
            if (
                allowedtypes is not None
                and self._annotations[annid].type not in allowedtypes
            ):
                continue
            yield self._annotations[annid]

    def reverse_iter(self, **kwargs):
        """
        Same as iter, but with the reverse parameter set to true.

        Args:
          kwargs: Same as for iter(), with revers=True fixed.
          **kwargs: will get passed on the Annotation.iter

        Returns:
          same result as iter()

        """
        return self.iter(reverse=True, **kwargs)

    def get(
        self, annid: Union[int, Annotation], default=None
    ) -> Union[Annotation, None]:
        """
        Gets the annotation with the given annotation id or returns the given default.

        NOTE: for handling cases where legacy code still expects the add method to return
        an id and not the annotation, this will accept an annotation so the the frequent
        pattern still works:

           annid = annset.add(b,e,t).id
           ann = annset.get(annid)

        If an annotation is passed the annotation from the set with the id of that annotation is
        returned, if the annotation is from that set, this will return the same object, if it is
        still in the set (or return the default value).

        Args:
          annid: the annotation id of the annotation to retrieve.
          default: what to return if an annotation with the given id is not
              found. (Default value = None)
          annid: Union[int:
          Annotation]:

        Returns:
          the annotation or the default value.

        """
        if isinstance(annid, Annotation):
            annid = annid.id
        return self._annotations.get(annid, default)

    def first(self):
        """
        Return the first (or only) annotation in the set by offset.

        Returns:
            first annotation

        """
        sz = len(self._annotations)
        if sz == 0:
            raise Exception("Empty set, there is no first annotation")
        elif sz == 1:
            return next(iter(self._annotations.values()))
        self._create_index_by_offset()
        _, _, annid = next(self._index_by_offset.irange(reverse=False))
        return self._annotations[annid]

    def last(self):
        """
        Return the last (or only) annotation by offset.

        Returns:
          last annotation

        """
        sz = len(self._annotations)
        if sz == 0:
            raise Exception("Empty set, there is no last annotation")
        elif sz == 1:
            return next(iter(self._annotations.values()))
        self._create_index_by_offset()
        _, _, annid = next(self._index_by_offset.irange(reverse=True))
        return self._annotations[annid]

    def for_idx(self, idx, default=None):
        """
        Return the annotation corresponding to the index idx in the set.
        This returns the
        annotation stored at the index, as added to the set. The order usually
        depends on the insertion time.
        If no annotation with the given index is specified, the value
        specified for `default` is returned.

        Args:
            idx:  index of the annotation in the set
            default: default value to return if now annotation with the given index exists

        Returns:
            the annotation with the given index or the default value
        """
        # TODO: we could make this more memory efficient (but slower) by
        # iterating over values until getting idxth
        tmplist = list(self._annotations.values())
        if idx < len(tmplist):
            return tmplist[idx]
        else:
            return default

    def __getitem__(self, annid):
        """
        Gets the annotation with the given annotation id or throws an exception.

        Args:
            annid: the annotation id

        Returns:
            annotation
        """
        return self._annotations[annid]

    def with_type(self, *anntype: Union[str, Iterable], non_overlapping: bool = False):
        """
        Gets annotations of the specified type(s).
        Creates the type index if necessary.

        Args:
          anntype: one or more types or type lists. The union of all types
              specified that way is used to filter the annotations. If no type
              is specified, all annotations are selected.

          non_overlapping: if True, only return annotations of any of the
              given types which do not overlap with other annotations. If
              there are several annotations that start at
              the same offset, use the type that comes first in the
              parameters, if there are more than one of that type, use the
              one that would come first in the usual sort order.

        Returns:
            a detached immutable annotation set with the matching annotations.
        """
        atypes = []
        for atype in anntype:
            if isinstance(atype, str):
                atypes.append(atype)
            else:
                for t in atype:
                    atypes.append(t)
        if not atypes:
            return self.detach()
        self._create_index_by_type()
        annids = set()
        for t in atypes:
            idxs = self._index_by_type.get(t)
            if idxs:
                annids.update(idxs)
        if non_overlapping:
            # need to get annotations grouped by start offset and sorted according to
            # what the Annotation class defines
            allanns = sorted(annids, key=lambda x: self._annotations[x])
            allanns = [self._annotations[x] for x in allanns]
            allannsgrouped = []
            curstart = None
            curset = None
            for ann in allanns:
                if curstart is None:
                    curset = [ann]
                    curstart = ann.start
                elif curstart == ann.start:
                    curset.append(ann)
                else:
                    allannsgrouped.append(curset)
                    curset = [ann]
                    curstart = ann.start
            if curset:
                allannsgrouped.append(curset)
            retanns = []
            # now go through all the grouped annoations and select the top priority one
            # then skip to the next group that does not overlap with the one we just selected
            typepriority = dict()
            for i, atype in enumerate(atypes):
                typepriority[atype] = len(atypes) - i
            curminoffset = 0
            for group in allannsgrouped:
                # instead of sorting, go through the group and find the top priority one
                topann = None
                if len(group) == 1:
                    if group[0].start >= curminoffset:
                        topann = group[0]
                elif len(group) == 0:
                    raise Exception("We should never get a 0 size group here!")
                else:
                    for i, ann in enumerate(group):
                        if ann.start >= curminoffset:
                            topann = ann
                            break
                    for ann in group[i + 1:]:
                        if ann.start < curminoffset:
                            continue
                        if typepriority[ann.type] > typepriority[topann.type]:
                            topann = ann
                        elif typepriority[ann.type] == typepriority[topann.type]:
                            if ann.end > topann.end:
                                topann = ann
                            elif ann.end == topann.end:
                                if ann.id > topann.id:
                                    topann = ann
                if topann is not None:
                    retanns.append(topann)
                    curminoffset = topann.end
            annids = [ann.id for ann in retanns]
        return self.detach(restrict_to=annids)

    def by_offset(self):
        """
        Yields lists of annotations which start at the same offset.
        """
        self._create_index_by_offset()
        lastoff = -1
        curlist = []
        for ann in self.iter():
            if ann.start != lastoff:
                if lastoff != -1:
                    yield curlist
                lastoff = ann.start
                curlist = [ann]
            else:
                curlist.append(ann)
        if lastoff != -1:
            yield curlist

    def by_span(self):
        """
        Yields list of annotations with identical spans. Note: first needs
        to sort all annotations!
        """
        self._create_index_by_offset()
        lastsoff = -1
        lasteoff = -1
        curlist = []
        for ann in self.iter_ol():
            if ann.start != lastsoff or ann.end != lasteoff:
                if lastsoff != -1:
                    yield curlist
                lastsoff = ann.start
                lasteoff = ann.end
                curlist = [ann]
            else:
                curlist.append(ann)
        if lastsoff != -1:
            yield curlist

    @property
    def type_names(self) -> KeysView[str]:
        """
        Gets the names of all types in this set. Creates the type index
        if necessary.
        """
        self._create_index_by_type()
        return self._index_by_type.keys()

    @support_annotation_or_set
    def startingat(
        self, start: int, ignored: Any = None, annid=None, include_self=False
    ):
        """
        Gets all annotations starting at the given offset (empty if none) and
        returns them in a detached annotation set.

        Note: this can be called with an annotation or annotation set instead
        of the start offset. If called with an annotation, this annotation is
        not included in the result set if `include_self` is `False`

        Args:
            start: the offset where annotations should start
            ignored: dummy parameter to allow the use of annotations and
                annotation sets
            annid:  dummy parameter to allow the use of annotations and
                annotation sets
            include_self:  should annotation passed be included in the result

        Returns:
            detached annotation set of matching annotations
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.starting_at(start)
        if not include_self and annid is not None:
            ignore = annid
        else:
            ignore = None
        return self._restrict_intvs(intvs, ignore=ignore)

    @support_annotation_or_set
    def start_min_ge(
        self, offset: int, ignored: Any = None, annid=None, include_self=False
    ):
        """Gets all annotations starting at the first possible offset
        at or after the given offset and returns them in an immutable
        annotation set.

        Args:
          offset: The offset
          ignored: dummy parameter to allow the use of annotations and
              annotation sets
          annid:  annotation id
          include_self: should annotation passed be included in the result

        Returns:
          annotation set of matching annotations

        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.starting_from(offset)
        # now select only those first ones which all have the same offset
        if not include_self and annid is not None:
            ignore = annid
        else:
            ignore = None
        retids = set()
        startoff = None
        for intv in intvs:
            if startoff is None:
                startoff = intv[0]
                if ignore is not None:
                    if ignore != intv[2]:
                        retids.add(intv[2])
                else:
                    retids.add(intv[2])
            elif startoff == intv[0]:
                if ignore is not None:
                    if ignore != intv[2]:
                        retids.add(intv[2])
                else:
                    retids.add(intv[2])
            else:
                break
        return self.detach(restrict_to=retids)

    @support_annotation_or_set
    def start_ge(self, start: int, ignored: Any = None, annid=None,
                 include_self=False):
        """
        Return the annotations that start at or after the given start offset.

        Args:
            start: Start offset
            ignored: dummy parameter to allow the use of annotations and
                annotation sets
            annid:  annotation id
            include_self:  should annotation passed be included in the result

        Returns:
          an immutable annotation set of the matching annotations

        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.starting_from(start)
        if not include_self and annid is not None:
            ignore = annid
        else:
            ignore = None
        return self._restrict_intvs(intvs, ignore=ignore)

    @support_annotation_or_set
    def start_lt(self, offset: int, ignored: Any = None, annid=None):
        """
        Returns the annotations that start before the given offset
        (or annotation). This also accepts an annotation or set.

        Args:
            offset: offset before which the annotations should start
            ignored: dummy parameter to allow the use of annotations and
                annotation sets
            annid:  annotation id

        Returns:
          an immutable annotation set of the matching annotations

        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.starting_before(offset)
        return self._restrict_intvs(intvs)

    @support_annotation_or_set
    def overlapping(self, start: int, end: int, annid=None, include_self=False):
        """
        Gets annotations overlapping with the given span. Instead of the
        start and end offsets,
        also accepts an annotation or annotation set.

        For each annotation ann in the result set, ann.overlapping(span)
        is True

        Args:
          start: start offset of the span
          end: end offset of the span
          annid: the annotation id of the annotation representing the span.
              (Default value = None)
          include_self: if True and the annotation id for the span is given,
              do not include that annotation in the result set.
              (Default value = False)

        Returns:
            an immutable annotation set with the matching annotations
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.overlapping(start, end)
        if not include_self and annid is not None:
            ignore = annid
        else:
            ignore = None
        return self._restrict_intvs(intvs, ignore=ignore)

    @support_annotation_or_set
    def covering(self, start: int, end: int, annid=None, include_self=False):
        """
        Gets the annotations which contain the given offset range
        (or annotation/annotation set), i.e. annotations such that the given
        offset range is within the annotation.

        For each annotation ann in the result set, ann.covering(span) is True.

        Args:
            start: the start offset of the span
            end: the end offset of the span
            annid: the annotation id of the annotation representing the span.
                (Default value = None)
            include_self: if True and the annotation id for the span is given,
                do not include that
                annotation in the result set. (Default value = False)

        Returns:
          an immutable annotation set with the matching annotations, if any
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.covering(start, end)
        if not include_self and annid is not None:
            ignore = annid
        else:
            ignore = None
        return self._restrict_intvs(intvs, ignore=ignore)

    @support_annotation_or_set
    def within(self, start: int, end: int, annid=None, include_self=False):
        """
        Gets annotations that fall completely within the given offset range,
        i.e. annotations such that the offset range is covering each of the
        annotation.

        For each annotation ann in the result set, ann.within(span) is True.

        Args:
            start: start offset of the range
            end: end offset of the range
            annid: the annotation id of the annotation representing the span.
                (Default value = None)
            include_self: if True and the annotation id for the span is given,
                do not include that
                annotation in the result set. (Default value = False)

        Returns:
            an immutable annotation set with the matching annotations
        """
        if start > end:
            raise Exception("Invalid offset range: {},{}".format(start, end))
        else:
            self._create_index_by_offset()
            intvs = self._index_by_offset.within(start, end)
        if not include_self and annid is not None:
            ignore = annid
        else:
            ignore = None
        return self._restrict_intvs(intvs, ignore=ignore)

    @support_annotation_or_set
    def coextensive(self, start: int, end: int, annid=None, include_self=False):
        """
        Returns a detached annotation set with all annotations that start and
        end at the given offsets.

        For each annotation ann in the result set, ann.coextensive(span) is True.

        Args:
          start: start offset of the span
          end: end offset of the span
          annid: the annotation id of the annotation representing the span.
              (Default value = None)
          include_self: if True and the annotation id for the span is given,
              do not include that annotation in the result set.

        Returns:
            annotation set with all annotations that have the same start
            and end offsets.
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.at(start, end)
        if not include_self and annid is not None:
            ignore = annid
        else:
            ignore = None
        return self._restrict_intvs(intvs, ignore=ignore)

    @support_annotation_or_set
    def before(
        self, start: int, end: int, annid=None, include_self=False, immediately=False
    ):
        """
        Returns a detached annotation set with all annotations that end
        before the given offsets.

        For each annotation ann in the result set, ann.isbefore(span) is True.

        Args:
            start: start offset of the span
            end: end offset of the span
            annid: the annotation id of the annotation representing the span.
                (Default value = None)
            include_self: if True and the annotation id for the span is given,
                do not include that annotation in the result set.
            immediately: if True, the end offset of the annotations return
                must coincide with the start offset of the span (default=False)

        Returns:
            annotation set with all annotations that end before the given span
        """
        self._create_index_by_offset()
        if immediately:
            intvs = self._index_by_offset.ending_at(start)
        else:
            intvs = self._index_by_offset.ending_to(start)
        # we need to filter self if self is zero-length!
        if not include_self and annid is not None:
            ignore = annid
        else:
            ignore = None
        return self._restrict_intvs(intvs, ignore=ignore)

    @support_annotation_or_set
    def after(
        self, start: int, end: int, annid=None, include_self=False, immediately=False
    ):
        """
        Returns a detached annotation set with all annotations that start
        after the given span.

        For each annotation ann in the result set, ann.isafter(span) is True.

        Args:
            start: start offset of the span
            end: end offset of the span
            annid: the annotation id of the annotation representing the span.
                (Default value = None)
            include_self: if True and the annotation id for the span is given,
                do not include that annotation in the result set.
            immediately: if True, the start offset of the annotations
                returned must coincide with the
                end offset of the span (default=False)

        Returns:
            annotation set with all annotations that start after the given span
        """
        self._create_index_by_offset()
        if immediately:
            intvs = self._index_by_offset.starting_at(end)
        else:
            intvs = self._index_by_offset.starting_from(end)
        # we need to filter self if self is zero-length!
        if not include_self and annid is not None:
            ignore = annid
        else:
            ignore = None
        return self._restrict_intvs(intvs, ignore=ignore)

    @property
    def span(self) -> Span:
        """
        Returns a tuple with the start and end offset the corresponds to the
        smallest start offset of any annotation
        and the largest end offset of any annotation.
        (Builds the offset index)
        """
        if len(self._annotations) == 0:
            return Span(0, 0)
        self._create_index_by_offset()
        return Span(self._index_by_offset.min_start(), self._index_by_offset.max_end())

    def __contains__(self, annorannid: Union[int, Annotation]) -> bool:
        """
        Provides 'annotation in annotation_set' functionality

        Args:
            :param annorannid: the annotation instance or annotation id to check

        Returns:
            `True` if the annotation exists in the set, `False` otherwise
        """
        if isinstance(annorannid, Annotation):
            return annorannid.id in self._annotations
        return (
            annorannid in self._annotations
        )  # On the off chance someone passed an ID in directly

    contains = __contains__

    def __repr__(self) -> str:
        """
        Returns the string representation of the set.
        """
        return "AnnotationSet({})".format(repr(list(self.iter())))

    def to_dict(self, anntypes=None, **kwargs):
        """
        Convert an annotation set to its dict representation.

        Args:
            anntypes: if not None, an iterable of annotation types to include
            **kwargs: passed on to the dict creation of contained annotations.

        Returns:
            the dict representation of the annotation set.
        """
        if anntypes is not None:
            anntypesset = set(anntypes)
            anns_list = list(
                val.to_dict(**kwargs)
                for val in self._annotations.values()
                if val.type in anntypesset
            )
        else:
            anns_list = list(
                val.to_dict(**kwargs) for val in self._annotations.values()
            )
        return {
            # NOTE: Changelog is not getting added as it is stored in the document part!
            "name": self.name,
            "annotations": anns_list,
            "next_annid": self._next_annid,
        }

    @staticmethod
    def from_dict(dictrepr, owner_doc=None, **kwargs):
        """
        Create an AnnotationSet from its dict representation and optionally
        set the owning document.

        Args:
          dictrepr: the dict representation of the annotation set
          owner_doc:  the owning document
          **kwargs: passed on to the creation of annotations

        Returns:
            the annotation set
        """
        annset = AnnotationSet(dictrepr.get("name"), owner_doc=owner_doc)
        annset._next_annid = dictrepr.get("next_annid")
        if dictrepr.get("annotations"):
            annset._annotations = dict(
                (int(a["id"]), Annotation.from_dict(a, owner_set=annset, **kwargs))
                for a in dictrepr.get("annotations")
            )
        else:
            annset._annotations = {}
        return annset

    @staticmethod
    def from_anns(anns, deep_copy=False, **kwargs):
        """
        Create a detached AnnotationSet from an iterable of annotations.

        Args:
          anns: an iterable of annotations
          deep_copy: if the annotations should get added as copies
              (default) or deep copies.

        Returns:
            the annotation set
        """
        annset = AnnotationSet(name="", owner_doc=None)
        annset._annotations = dict()
        maxid = 0
        for ann in anns:
            if deep_copy:
                addann = ann.deepcopy()
            else:
                addann = ann.copy()
            annset._annotations[addann.id] = addann
            if addann.id > maxid:
                maxid = addann.id
        annset._next_annid = maxid
        annset._is_immutable = True

        return annset
