

class ChangeLog:
    def __init__(self, document):
        self.log = []
        self.offsetformat = "python"
        self.document = document

    def append(self, element):
        assert isinstance(element, dict)
        self.log.append(element)

    def __len__(self):
        return len(self.log)

