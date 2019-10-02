from .document import OFFSET_TYPE_PYTHON, OFFSET_TYPE_JAVA
import gatenlp

class ChangeLog:
    def __init__(self, document):
        self.log = []
        self.offset_type = OFFSET_TYPE_PYTHON
        self.document = document

    def append(self, element):
        assert isinstance(element, dict)
        self.log.append(element)

    def __len__(self):
        return len(self.log)

    def json_repr(self, **kwargs):
        # TODO: if we have the offset_type kwarg and we need to convert offsets, create a copy of the
        # chencges on the fly after creating the OffsetMapping and include that copy together with the
        # changed offset type
        return {
            "object_type": "gatenlp.changelog.ChangeLog",
            "gatenlp_version": gatenlp.__version__,
            "changes": self.log,
            "offset_type": self.offset_type
        }