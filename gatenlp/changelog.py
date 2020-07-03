from typing import List, Callable, Dict
import sys
from gatenlp.offsetmapper import OffsetMapper, OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
import importlib

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

    def _fixup_changes(self, method: Callable, replace=False) -> List[Dict]:
        """
        In-place modify the annotation offsets of the changes according to
        the given method.
        :param method: an object method method for converting offsets from or to python.
        :param replace: if True, modifies the original change objects in the changelog, otherwise, uses copies
        :return: the modified changes, a reference to the modified changes list of the instance
        """
        if not replace:
            newchanges = []
        for change in self.changes:
            if not replace:
                chg = dict(change)
            else:
                chg = change
            if "start" in change:
                chg["start"] = method(change["start"])
            if "end" in change:
                chg["end"] = method(change["end"])
            if not replace:
                newchanges.append(chg)
        if replace:
            return self.changes
        else:
            return newchanges

    def fixup_changes(self, offset_mapper, offset_type, replace=True):
        """
        Update the offsets of all annotations in this changelog to the desired
        offset type, if necessary. If the ChangeLog already has that offset type, this does nothing.

        :param offset_mapper: a prepared offset mapper to use
        :param offset_type: the desired offset type
        :param replace: if True, replaces the original offsets in the original change objects, otherwise creates
          new change objects and a new changes list and returs it.
        :return: a reference to the modified changes
        """
        if offset_type != self.offset_type:
            if offset_type == OFFSET_TYPE_JAVA:
                method = offset_mapper.convert_to_java
            elif offset_type == OFFSET_TYPE_PYTHON:
                method = offset_mapper.convert_to_python
            else:
                raise Exception("Not a proper offset type: {}".format(offset_type))
            if replace:
                self.offset_type = offset_type
            return self._fixup_changes(method, replace=replace)
        else:
            return self.changes

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

    def to_dict(self, **kwargs):
        offset_type = self.offset_type
        changes = self.changes
        if "offset_type" in kwargs and kwargs["offset_type"] != offset_type:
            om = kwargs.get("offset_mapper")
            if om is None:
                raise Exception("Need to convert offsets, but no offset_mapper parameter given")
            offset_type = kwargs["offset_type"]
            if offset_type == OFFSET_TYPE_JAVA:
                changes = self._fixup_changes(om.convert_to_java, replace=False)
            else:
                changes = self._fixup_changes(om.convert_to_python, replace=False)
        return {
            "changes": changes,
            "offset_type": offset_type
        }

    @staticmethod
    def from_dict(dictrepr, **kwargs):
        if dictrepr is None:
            return None
        cl = ChangeLog()
        cl.changes = dictrepr.get("changes")
        cl.offset_type = dictrepr.get("offset_type")
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

    def save(self, whereto, fmt="json", offset_type=None, offset_mapper=None, mod="gatenlp.serialization.default", **kwargs):
        """
        Save the document in the given format.

        Additional keyword parameters for format "json":
        * as_array: boolean, if True stores as array instead of dictionary, using to


        :param whereto: either a file name or something that has a write(string) method.
        :param fmt: serialization format, one of "json", "msgpack" or "pickle"
        :param offset_type: store using the given offset type or keep the current if None
        :param offset_mapper: nedded if the offset type should get changed
        :param mod: module to use
        :param kwargs: additional parameters for the format
        :return:
        """
        m = importlib.import_module(mod)
        ser = m.FORMATS[fmt]
        ser.save(ChangeLog, self, to_file=whereto, offset_type=offset_type, offset_mapper=offset_mapper, **kwargs)

    def save_mem(self, fmt="json", offset_type=None, offset_mapper=None, mod="gatenlp.serialization.default", **kwargs):
        """
        Serialize and save to a string.

        Additional keyword parameters for format "json":
        * as_array: boolean, if True stores as array instead of dictionary, using to


        :param fmt: serialization format, one of "json", "msgpack" or "pickle"
        :param offset_type: store using the given offset type or keep the current if None
        :param offset_mapper: nedded if the offset type should get changed
        :param mod: module to use
        :param kwargs: additional parameters for the format
        :return:
        """
        m = importlib.import_module(mod)
        ser = m.FORMATS[fmt]
        return ser.save(ChangeLog, self, to_mem=True, offset_type=offset_type, offset_mapper=offset_mapper, **kwargs)

    @staticmethod
    def load(wherefrom, fmt="json", offset_mapper=None, mod="gatenlp.serialization.default", **kwargs):
        """

        :param wherefrom:
        :param fmt:
        :param offset_mapper: offset mapper in case the offsets need to get converted
        :param kwargs:
        :return:
        """
        m = importlib.import_module(mod)
        ser = m.FORMATS[fmt]
        doc = ser.load(ChangeLog, from_file=wherefrom, offset_mapper=offset_mapper, **kwargs)
        if doc.offset_type == OFFSET_TYPE_JAVA:
            doc.to_type(OFFSET_TYPE_PYTHON)
        return doc

    @staticmethod
    def load_mem(wherefrom, fmt="json", offset_mapper=None, mod="gatenlp.serialization.default", **kwargs):
        """

        Note: the offset type is always converted to PYTHON when loading!

        :param wherefrom: the string to deserialize
        :param fmt:
        :param offset_mapper: offset mapper in case the offsets need to get converted
        :param kwargs:
        :return:
        """
        m = importlib.import_module(mod)
        ser = m.FORMATS[fmt]
        doc = ser.load(ChangeLog, from_mem=wherefrom, offset_mapper=offset_mapper, **kwargs)
        if doc.offset_type == OFFSET_TYPE_JAVA:
            doc.to_type(OFFSET_TYPE_PYTHON)
        return doc