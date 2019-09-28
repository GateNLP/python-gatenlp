"""
An annotation is immutable, but the features it contains are mutable.
"""
from .feature_map import FeatureMap

# TODO: make it sortable!
class Annotation:
    def __init__(self, annot_type, start, end, annot_id, annotationset=None, changelogger=None, initialfeatures=None):
        self.changelogger = changelogger
        self.type = annot_type
        self.start = start
        self.end = end
        self.features = FeatureMap(changelogger=changelogger, owner_set=annotationset,
                                   owner_id=id, initialfeatures=initialfeatures)
        self.id = annot_id

    def __eq__(self, other):
        if hasattr(other, "id"):
            return self.id == other.id
        else:
            return False

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return "Annotation<({},{},{},id={})>".format(self.type, self.start, self.end, self.id)
