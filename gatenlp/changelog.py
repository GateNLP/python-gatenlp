from typing import List, Callable, Dict
import sys
from gatenlp.offsetmapper import OffsetMapper, OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
import importlib

# TODO: allow to add handlers for each action or a set or all actions
# TODO: review actions, different action for set document feature and set annotation feature?

ACTION_DEL_DOC_FEATURE = "doc-feature:remove"
ACTION_SET_DOC_FEATURE = "doc-feature:set"
ACTION_CLEAR_DOC_FEATURES = "doc-features:clear"
ACTION_DEL_ANN_FEATURE = "ann-feature:remove"
ACTION_SET_ANN_FEATURE = "ann-feature:set"
ACTION_CLEAR_ANN_FEATURES = "ann-features:clear"
ACTION_REMOVE_ANNSET = "annotations:remove"
ACTION_ADD_ANNSET = "annotations:remove"
ACTION_ADD_ANN = "annotation:add"
ACTION_DEL_ANN = "annotation:remove"
ACTION_CLEAR_ANNS = "annotations:clear"

ACTIONS = {
    ACTION_DEL_DOC_FEATURE,
    ACTION_SET_DOC_FEATURE,
    ACTION_CLEAR_DOC_FEATURES,
    ACTION_DEL_ANN_FEATURE,
    ACTION_SET_ANN_FEATURE,
    ACTION_CLEAR_ANN_FEATURES,
    ACTION_REMOVE_ANNSET,
    ACTION_ADD_ANNSET,
    ACTION_ADD_ANN,
    ACTION_DEL_ANN,
    ACTION_CLEAR_ANNS
}

# flags that describe how to handle adding an annotation to a document from a changelog if an annotation
# with the same annotation id already exists in the set.
ADDANN_REPLACE_ANNOTATION = "replace-annotation" # completely replace with the new one
ADDANN_REPLACE_FEATURES = "replace-features" # just completely replace the features
ADDANN_UPDATE_FEATURES = "update-features" # add new and update existing features, do not delete any
ADDANN_ADD_NEW_FEATURES = "add-new-features" # only add new features
ADDANN_IGNORE = "ignore" # ignore that annotation, do nothing
ADDANN_ADD_WITH_NEW_ID = "add-with-new-id"  # add that annotation with a new id to the set


class ChangeLog:
    def __init__(self, store=True):
        """

        :param store: if True, the change log stores the actions it receives (default). This can be set
          to false if only callbacks are needed.
        """
        self.gatenlp_type = "ChangeLog"
        self.changes = []
        self.offset_type = OFFSET_TYPE_PYTHON
        self._handlers = dict()
        self._store = store

    def add_handler(self, actions, handler):
        """
        Register a handler to get called back when any of the actions is added.
        If any handler was already registered for one or more of the actions, the new handler overrides it.

        :param actions: either a single action string or a collection of several action strings
        :param handler: a callable that takes the change information
        :return:
        """
        if isinstance(actions, str):
            actions = [actions]
        for a in actions:
            if a not in ACTIONS:
                raise Exception(f"Action {a} not known, cannot add handler")
            self._handlers[a] = handler

    def append(self, change: Dict):
        assert isinstance(change, dict)
        action = change.get("command",None)
        if action is None:
            raise Exception("Odd change, does not have 'command' key")
        if self._store:
            self.changes.append(change)
        hndlr = self._handlers.get(action)
        if hndlr:
            hndlr()

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
        saver = m.get_changelog_saver(whereto, fmt)
        saver(ChangeLog, self, to_file=whereto, offset_type=offset_type, offset_mapper=offset_mapper, **kwargs)

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
        saver = m.get_changelog_saver(None, fmt)
        return saver(ChangeLog, self, to_mem=True, offset_type=offset_type, offset_mapper=offset_mapper, **kwargs)

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
        loader = m.get_changelog_loader(wherefrom, fmt)
        chl = loader(ChangeLog, from_file=wherefrom, offset_mapper=offset_mapper, **kwargs)
        if chl.offset_type == OFFSET_TYPE_JAVA:
            chl.fixup_changes(offset_mapper, offset_type=OFFSET_TYPE_PYTHON, replace=True)
        return chl

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
        loader = m.get_changelog_loader(None, fmt)
        chl = loader(ChangeLog, from_mem=wherefrom, offset_mapper=offset_mapper, **kwargs)
        if chl.offset_type == OFFSET_TYPE_JAVA:
            chl.fixup_changes(offset_mapper, offset_type=OFFSET_TYPE_PYTHON, replace=True)
        return chl

    def pprint(self, out=None):
        """
        Pretty print to the given output stream, sys.stdout if not given.
        :return:
        """
        if out is None:
            out = sys.stdout
        print("ChangeLog(", file=out)
        for i, c in enumerate(self.changes):
            cmd = c.get("command")
            parms = c.copy()
            del parms["command"]
            print(f"{i}: cmd={cmd} {parms}")
        print(")")