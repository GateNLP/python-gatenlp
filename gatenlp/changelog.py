from typing import List, Callable, Dict
from gatenlp.offsetmapper import OffsetMapper, OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON


class ChangeLog:
    def __init__(self):
        self.gatenlp_type = "ChangeLog"
        self.changes = []
        self.offset_type = OFFSET_TYPE_PYTHON

    def append(self, element: Dict):
        assert isinstance(element, dict)
        self.changes.append(element)

    def __len__(self) -> int:
        return len(self.changes)

    def _fixup_changes(self, method: Callable) -> List[Dict]:
        """
        In-place modify the annotation offsets of the changes according to
        the given method.
        :param method: an object method method for converting offsets from or to python.
        :return: the modified changes, a reference to the modified changes list of the instance
        """
        for change in self.changes:
            if "start" in change:
                change["start"] = method(change["start"])
            if "end" in change:
                change["end"] = method(change["end"])
        return self.changes

    def fixup_changes(self, offset_mapper, offset_type):
        """
        In-place update the offsets of all annotations in this changelog to the desired
        offset type, if necessary. If the ChangeLog already has that offset type, this does nothing.
        :param offset_mapper: a prepared offset mapper to use
        :param offset_type: the desired offset type
        :return: a reference to the modified changes
        """
        if offset_type != self.offset_type:
            if offset_type == OFFSET_TYPE_JAVA:
                method = offset_mapper.convert_to_java
            elif offset_type == OFFSET_TYPE_PYTHON:
                method = offset_mapper.convert_to_python
            else:
                raise Exception("Not a proper offset type: {}".format(offset_type))
            return self._fixup_changes(method)

    def __repr__(self) -> str:
        return "ChangeLog([{}])".format(",".join([str(c) for c in self.changes]))

    def format_to(self, fp, prefix="") -> None:
        for c in self.changes:
            print(prefix, str(c), sep="", file=fp)

    def _json_repr(self, **kwargs) -> Dict:
        offset_type = self.offset_type
        changes = self.changes
        if "offset_type" in kwargs and kwargs["offset_type"] != offset_type:
            om = kwargs.get("offset_mapper")
            if om is None:
                raise Exception("Need to convert offsets, but no offset_mapper parameter given")
            offset_type = kwargs["offset_type"]
            if offset_type == OFFSET_TYPE_JAVA:
                changes = self._fixup_changes(om.convert_to_java)
            else:
                changes = self._fixup_changes(om.convert_to_python)
        return {
            "changes": changes,
            "offset_type": offset_type,
            "gatenlp_type": self.gatenlp_type
        }

    @staticmethod
    def _from_json_map(jsonmap, **kwargs) -> "ChangeLog":
        cl = ChangeLog()
        cl.changes = jsonmap.get("changes")
        cl.offset_type = jsonmap.get("offset_type")
        if cl.offset_type == OFFSET_TYPE_JAVA:
            # we need either an offset mapper or a document
            if "offset_mapper" in kwargs:
                om = kwargs.get("offset_mapper")
            elif "document" in kwargs:
                om = OffsetMapper(kwargs.get("document"))
            else:
                raise Exception("Loading a changelog with offset_type JAVA, need kwarg 'offset_mapper' or 'document'")
            cl._fixup_changes(om.convert_to_python)
        return cl
