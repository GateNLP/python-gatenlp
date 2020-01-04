from typing import List, Tuple, Union, Dict, Set, KeysView, Iterator, Generator
from collections import defaultdict
from gatenlp.annotation import Annotation
from gatenlp.exceptions import InvalidOffsetException
from gatenlp.changelog import ChangeLog
from gatenlp.impl import SortedIntvls
import numbers
from functools import wraps


def support_annotation_or_set(method):
    """
    Decorator to allow a method that normally takes a start and end
    offset to take an annotation or annotation set or a pair of offsets instead.
    It also allows to take a single offset instead which will then be used as both start and end offset.
    """
    @wraps(method)
    def _support_annotation_or_set(self, *args):
        if len(args) == 1:
            if isinstance(args[0], Annotation):
                left, right = args[0].start, args[0].end
            elif isinstance(args[0], AnnotationSet):
                left, right = args[0].span()
            elif isinstance(args[0], (tuple, list)) and len(args[0]) == 2:
                left, right = args[0]
            elif isinstance(args[0], numbers.Integral):
                left, right = args[0], args[0]+1
            else:
                raise Exception("Not an annotation or an annotation set or pair: {}".format(args[0]))
        else:
            assert len(args) == 2
            left, right = args

        return method(self, left, right)

    return _support_annotation_or_set


class AnnotationSet:
    def __init__(self, name: str = "", changelog: ChangeLog = None, owner_doc: "Document" = None):
        """
        Create a new annotation set.

        :param name: the name of the annotation set. This is only really needed if the changelog is used.
        :param changelog: if a changelog is used, then all changes to the set and its annotations are logged
        :param owner_doc: if this is set, the set and all sets created from it can be queried for the
        owning document and offsets get checked against the text of the owning document, if it has
        text.
        """
        # print("CREATING annotation set {} with changelog {} ".format(name, changelog), file=sys.stderr)
        self.gatenlp_type = "AnnotationSet"
        self.changelog = changelog
        self.name = name
        self.owner_doc = owner_doc

        # NOTE: the index is only created when we actually need it!
        self._index_by_offset: SortedIntvls = None
        self._index_by_type = None
        # internally we represent the annotations as a map from annotation id (int) to Annotation
        self._annotations = {}
        self._is_immutable = False
        self._next_annid = 0

    def __setattr__(self, key, value):
        """
        Prevent immutable fields from getting overridden, once they have been
        set.
        :param key: attribute to set
        :param value: value to set attribute to
        :return:
        """
        if key == "gatenlp_type" or key == "name" or key == "owner_doc":
            if self.__dict__.get(key, None) is None:
                super().__setattr__(key, value)
            else:
                raise Exception("AnnotationSet attribute cannot get changed after being set")
        else:
            super().__setattr__(key, value)

    def restrict(self, restrict_to=None) -> "AnnotationSet":
        """
        Create an immutable copy of this set, optionally restricted to the given annotation ids.

        :param restrict_to: an iterable of annotation ids
        :return: an immutable annotation set with all the annotations of this set or restricted to the ids
          in restrict_to
        """
        annset = AnnotationSet(name="", owner_doc=self.owner_doc)
        annset._is_immutable = True
        annset._annotations = {annid: self._annotations[annid] for annid in restrict_to}
        annset._next_annid = self._next_annid
        return annset

    def _create_index_by_offset(self) -> None:
        """
        Generates the offset index, if it does not already exist.
        The offset index is an interval tree that stores the annotation ids for the offset interval of the annotation.
        """
        if self._index_by_offset is None:
            self._index_by_offset = SortedIntvls()
            for ann in self._annotations.values():
                self._index_by_offset.add(ann.start, ann.end, ann.id)

    def _create_index_by_type(self) -> None:
        """
        Generates the type index, if it does not already exist. The type index is a map from
        annotation type to a set of all annotation ids with that type.
        """
        if self._index_by_type is None:
            self._index_by_type = defaultdict(set)
            for ann in self._annotations.values():
                self._index_by_type[ann.type].add(ann.id)

    def _add_to_indices(self, annotation: Annotation) -> None:
        """
        If we have created the indices, add the annotation to them.

        :param annotation: the annotation to add to the indices.
        :return:
        """
        if self._index_by_type is not None:
            self._index_by_type[annotation.type].add(annotation.id)
        if self._index_by_offset is not None:
            self._index_by_offset.add(annotation.start, annotation.end, annotation.id)

    def _remove_from_indices(self, annotation: Annotation) -> None:
        """
        Remove an annotation from the indices.

        :param annotation: the annotation to remove.
        :return:
        """
        if self._index_by_offset is not None:
            self._index_by_offset.remove(annotation.start, annotation.end, annotation.id)
        if self._index_by_type is not None:
            self._index_by_type[annotation.type].remove(annotation.id)

    @staticmethod
    def _intvs2idlist(intvs) -> List[int]:
        """
        Convert an iterable of interval tuples (start, end, id) to a list of ids

        :param intvs: iterable of interval tuples
        :return: list of ids
        """
        return [i[2] for i in intvs]

    @staticmethod
    def _intvs2idset(intvs) -> Set[int]:
        """
        Convert an iterable of interval tuples (start, end, id) to a set of ids

        :param intvs: iterable of interval tuples
        :return: set of ids
        """
        ret = set()
        for i in intvs:
            ret.add(i[2])
        return ret

    def _restrict_intvs(self, intvs) -> "AnnotationSet":
        return self.restrict(AnnotationSet._intvs2idlist(intvs))

    def __len__(self) -> int:
        """
        Return number of annotations in the set.

        :return: number of annotations
        """
        return len(self._annotations)

    def size(self) -> int:
        """
        Return number of annotations in the set.

        :return: number of annotations
        """
        return len(self._annotations)

    def get_doc(self) -> Union["Document", None]:
        """
        Get the owning document, if known. If the owning document was not set, return None.

        :return: the document this annotation set belongs to or None if unknown.
        """
        return self.owner_doc

    @support_annotation_or_set
    def _check_offsets(self, start: int, end: int) -> None:
        """
        Checks the offsets for the given annotation against the document boundaries, if we know the owning
        document and if the owning document has text.
        """
        if self.owner_doc is None:
            return
        if self.owner_doc.text is None:
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

    def add(self, start: int, end: int, anntype: str, features, annid: int = None):
        """
        Add an annotation to the set. Once an annotation has been added, the start and end offsets,
        the type, and the annotation id are immutable.

        :param start: start offset
        :param end: end offset
        :param anntype: the annotation type
        :param features: a map, an iterable of tuples or an existing feature map. In any case, the features are
        used to create a new feature map for this annotation.
        :param annid: the annotation id, if not specified the next free one for this set is used.
        NOTE: the id should normally left unspecified and get assigned automatically.
        :return: the annotation id of the added annotation
        """
        if self._is_immutable:
            raise Exception("Cannot add an annotation to an immutable annotation set")
        self._check_offsets(start, end)
        if annid and annid in self._annotations:
            raise Exception("Cannot add annotation with id {}, already in set".format(annid))
        if annid is None:
            annid = self._next_annid
            self._next_annid = self._next_annid + 1
        ann = Annotation(start, end, anntype, annid, owner_set=self,
                         changelog=self.changelog, features=features)
        self._annotations[annid] = ann
        self._add_to_indices(ann)
        if self.changelog is not None:
            self.changelog.append({
                "command": "annotation:add",
                "set": self.name,
                "start": ann.start,
                "end": ann.end,
                "type": ann.type,
                "features": ann.features,
                "id": ann.id})
        return ann.id

    def add_ann(self, ann, annid: int = None):
        """
        Add a copy of the given ann to the annotation set, either with a new annotation id or
        with the one given.
        :param annid: the annotation id, if not specified the next free one for this set is used.
        NOTE: the id should normally left unspecified and get assigned automatically.
        :return: the annotation id of the added annotation
        """
        return self.add(ann.start, ann.end, ann.type, ann.features(), annid=annid)

    def remove(self, annotation: Union[int, Annotation]) -> None:
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
        if self.changelog is not None:
            self.changelog.append({
                "command": "annotation:remove",
                "set": self.name,
                "id": annid})
        self._remove_from_indices(annotation)

    def clear(self) -> None:
        """
        Remove all annotations from the set.

        :return:
        """
        self._annotations.clear()
        self._index_by_offset = None
        self._index_by_type = None
        if self.changelog is not None:
            self.changelog.append({
                "command": "annotations:clear",
                "set": self.name})

    def __iter__(self) -> Iterator:
        """
        Iterator for going through all the annotations of the set.

        :return: a generator for the annotations in document order
        """
        # return iter(self._annotations.values())
        return self.in_document_order()

    def in_document_order(self, *annotations, from_offset: Union[int, None] = None,
                          to_offset: Union[None, int] = None,
                          reverse: bool = False, anntype: str = None) -> Generator:
        """
        Returns a generator for going through annotations in document order. If an iterator of annotations
        is given, then those annotations, optionally limited by the other parameters are returned in
        document order, otherwise, all annotations in the set are returned, otionally limited by the other
        parameters.

        :param annotations: either missing or exactly one parameter which must be an iterable of annotations
          from this annotation set.
        :param from_offset: the offset from where to start including annotations
        :param to_offset: the last offset to use as the starting offset of an annotation
        :param anntype: only annotations of this type
        :param reverse: process in reverse document order
        :return: generator for annotations in document order
        """
        if from_offset is not None:
            assert from_offset >= 0
        if to_offset is not None:
            assert to_offset >= 1
        if to_offset is not None and from_offset is not None:
            assert to_offset > from_offset
        if len(annotations) == 0:  # no annotations given, we use the ones in the set
            self._create_index_by_offset()
            for _start, _end, annid in self._index_by_offset.irange(minoff=from_offset, maxoff=to_offset, reverse=reverse):
                if anntype is not None and self._annotations[annid].type != anntype:
                    continue
                yield self._annotations[annid]
        elif len(annotations) == 1:
            for ann in sorted(annotations, reverse=reverse, key=lambda x: (x.start, x.end)):
                if anntype is not None and ann.type != anntype:
                    continue
                if from_offset is not None and ann.start < from_offset:
                    continue
                if to_offset is not None and ann.start > to_offset:
                    continue
                yield ann

    def get(self, annid: int, default=None) -> Union[Annotation, None]:
        """
        Gets the annotation with the given annotation id or returns the given default.

        :param annid: the annotation id of the annotation to retrieve.
        :param default: what to return if an annotation with the given id is not found.
        :return: the annotation or the default value.
        """
        return self._annotations.get(annid, default)

    def all_by_type(self, anntype: Union[str, None] = None) -> "AnnotationSet":
        """
        Gets annotations of the specified type. If the anntype is None, return all annotation in an immutable set.
        Creates the type index if necessary.

        :param anntype: if specified, the type of the annotations to return, of None, all annotations are selected.
        :return: an immutable annotation set with the matching annotations.
        """
        self._create_index_by_type()
        if anntype is None:
            annids = self._annotations.keys()
        else:
            annids = self._index_by_type.get(anntype, None)
            if annids is None:
                annids = []
        return self.restrict(annids)

    def type_names(self) -> KeysView[str]:
        """
        Gets the names of all types in this set. Creates the type index if necessary.

        :return: the set of known annotation type names.
        """
        self._create_index_by_type()
        return self._index_by_type.keys()

    def starting_at(self, start: int) -> "AnnotationSet":
        """
        Gets all annotations starting at the given offset (empty if none) and returns them in an immutable
        annotation set.

        :param start: the offset where annotations should start
        :return: annotation set of matching annotations
        """
        # NOTE: my assumption about how intervaltree works was wrong, so we need to filter what we get from the
        # point query
        self._create_index_by_offset()
        intvs = self._index_by_offset.starting_at(start)
        return self._restrict_intvs(intvs)

    def first_from(self, offset: int) -> "AnnotationSet":
        """
        Gets all annotations at the first valid position at or after the given offset and returns them in an immutable
        annotation set.

        :param offset: The offset
        :return: annotation set of matching annotations
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.starting_from(offset)
        # now select only those first ones which all have the same offset
        retids = set()
        startoff = None
        for intv in intvs:
            if startoff is None:
                startoff = intv[0]
                retids.add(intv[2])
            elif startoff == intv[0]:
                retids.add(intv[2])
            else:
                break
        return self.restrict(retids)

    @support_annotation_or_set
    def overlapping(self, start: int, end: int) -> "AnnotationSet":
        """
        Gets annotations overlapping with the given span. Instead of the start and end offsets,
        also accepts an annotation or annotation set.

        :param start: start offset of the span
        :param end: end offset of the span
        :return: an immutable annotation set with the matching annotations
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.overlap(start, end)
        return self._restrict_intvs(intvs)

    @support_annotation_or_set
    def covering(self, start: int, end: int) -> "AnnotationSet":
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
        intvs = self._index_by_offset.covering(start, end)
        return self._restrict_intvs(intvs)

    @support_annotation_or_set
    def within(self, start: int, end: int) -> "AnnotationSet":
        """
        Gets annotations that fall completely within the given offset range

        :param start: start offset of the range
        :param end: end offset of the range
        :return: an immutable annotation set with the matching annotations
        """
        if start == end:
            intvs = []
        elif start > end:
            raise Exception("Invalid offset range: {},{}".format(start, end))
        else:
            self._create_index_by_offset()
            intvs = self._index_by_offset.within(start, end)
        return self._restrict_intvs(intvs)

    def starting_from(self, start: int) -> "AnnotationSet":
        """
        Return the annotations that start at or after the given start offset.

        :param start: Start offset
        :return: an immutable annotation set of the matching annotations
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.starting_from(start)
        return self._restrict_intvs(intvs)

    def starting_before(self, offset: int) -> "AnnotationSet":
        """
        Return the annotations that start before the given offset (or annotation). This also accepts an annotation
        or set.

        :param offset: offset before which the annotations should start
        :return: an immutable annotation set of the matching annotations
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.starting_before(offset)
        return self._restrict_intvs(intvs)

    def coextensive(self, start: int, end: int) -> "AnnotationSet":
        """
        Return an immutable annotation set with all annotations that start and end at the given offsets.

        :param start: start offset of the span
        :param end: end offset of the span
        :return: annotation set with all annotations that have the same start and end offsets.
        """
        self._create_index_by_offset()
        intvs = self._index_by_offset.at(start, end)
        return self._restrict_intvs(intvs)

    def span(self) -> Tuple[int, int]:
        """
        Returns a tuple with the start and end offset the corresponds to the smallest start offset of any annotation
        and the largest end offset of any annotation.
        (Builds the offset index)

        :return: tuple of minimum start offset and maximum end offset
        """
        self._create_index_by_offset()
        return self._index_by_offset.min_start(), self._index_by_offset.max_end()

    def __contains__(self, annorannid: Union[int, Annotation]) -> bool:
        """
        Provides 'annotation in annotation_set' functionality

        :param annorannid: the annotation instance or annotation id to check
        :return: true if the annotation exists in the set, false otherwise
        """
        if isinstance(annorannid, Annotation):
            return annorannid.id in self._annotations
        return annorannid in self._annotations  # On the off chance someone passed an ID in directly

    contains = __contains__

    def __repr__(self) -> str:
        """
        String representation of the set.

        :return: string representation.
        """
        return "AnnotationSet({})".format(repr(list(self.in_document_order())))

    def _json_repr(self, **kwargs) -> Dict:
        return {
            "annotations": [ann._json_repr(**kwargs) for ann in self._annotations.values()],
            "next_annid": self._next_annid,
            "name": self.name,
            "gatenlp_type": self.gatenlp_type
        }

    @staticmethod
    def _from_json_map(jsonmap, **kwargs) -> "AnnotationSet":
        annset = AnnotationSet(name=jsonmap.get("name"))
        annmap = {}
        for ann in jsonmap.get("annotations"):
            ann._owner_set = annset
            annmap[ann.id] = ann
        annset._annotations = annmap
        annset._next_annid = jsonmap.get("next_annid")
        return annset

