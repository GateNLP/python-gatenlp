"""
Module for defining the constants used in the changelog module
"""

ACTION_DEL_DOC_FEATURE = "doc-feature:remove"
ACTION_SET_DOC_FEATURE = "doc-feature:set"
ACTION_CLEAR_DOC_FEATURES = "doc-features:clear"
ACTION_DEL_ANN_FEATURE = "ann-feature:remove"
ACTION_SET_ANN_FEATURE = "ann-feature:set"
ACTION_CLEAR_ANN_FEATURES = "ann-features:clear"
ACTION_REMOVE_ANNSET = "annotations:remove"
ACTION_ADD_ANNSET = "annotations:add"
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
    ACTION_CLEAR_ANNS,
}

# flags that describe how to handle adding an annotation to a document from a changelog if an
# annotation with the same annotation id already exists in the set.
ADDANN_REPLACE_ANNOTATION = "replace-annotation"  # completely replace with the new one
ADDANN_REPLACE_FEATURES = "replace-features"  # just completely replace the features
ADDANN_UPDATE_FEATURES = (
    "update-features"  # add new and update existing features, do not delete any
)
ADDANN_ADD_NEW_FEATURES = "add-new-features"  # only add new features
ADDANN_IGNORE = "ignore"  # ignore that annotation, do nothing
ADDANN_ADD_WITH_NEW_ID = (
    "add-with-new-id"  # add that annotation with a new id to the set
)

__all__ = [
    "ACTIONS",
    "ACTION_ADD_ANN",
    "ACTION_ADD_ANNSET",
    "ACTION_CLEAR_ANNS",
    "ACTION_CLEAR_ANN_FEATURES",
    "ACTION_CLEAR_DOC_FEATURES",
    "ACTION_DEL_ANN",
    "ACTION_DEL_ANN_FEATURE",
    "ACTION_DEL_DOC_FEATURE",
    "ACTION_REMOVE_ANNSET",
    "ACTION_SET_ANN_FEATURE",
    "ACTION_SET_DOC_FEATURE",
    "ADDANN_ADD_NEW_FEATURES",
    "ADDANN_ADD_WITH_NEW_ID",
    "ADDANN_IGNORE",
    "ADDANN_REPLACE_ANNOTATION",
    "ADDANN_REPLACE_FEATURES",
]
