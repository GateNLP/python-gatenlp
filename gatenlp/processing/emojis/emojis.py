"""
Module that implements the EmojiAnnotator.
Emoji information has been converted from https://github.com/eliasdabbas/advertools
"""
import os
import json
import re
from gatenlp.processing.annotator import Annotator

PATH_E2I = os.path.join(os.path.dirname(__file__), "emojis2info.json")
PATH_ER = os.path.join(os.path.dirname(__file__), "emojiregex.txt")

# load the emoji info when the module is loaded and share the info among all annotators
with open(PATH_E2I, "rt", encoding="utf-8") as infp:
    EMOJI2INFO = json.load(infp)

with open(PATH_ER, "rt", encoding="utf-8") as infp:
    PAT_EMOJI_STR = infp.readline().strip("\n\r")

PAT_EMOJI = re.compile(PAT_EMOJI_STR, re.UNICODE)


class EmojiAnnotator(Annotator):
    """
    Annotator to find emojis in the document text.
    """
    def __init__(self, outset_name="", ann_type="Emoji", string_feature=None):
        """
        Initialize the Emoji annotator. For each emoji found, an annotation is created which
        contains the features codepoint, status, name, group, subgroup.

        Args:
            outset_name: the name of the output annotation set
            ann_type: the annotation type for the annotations to create
            string_feature: if None, the original matched string is not added as a feature, otherwise, the
                name of the feature to use for adding.
        """
        self.outset_name = outset_name
        self.ann_type = ann_type
        self.string_feature = string_feature

    def __call__(self, doc, **kwargs):
        txt = doc.text
        if txt is None:
            return doc
        outset = doc.annset(self.outset_name)
        for m in re.finditer(PAT_EMOJI, txt):
            infos = EMOJI2INFO.get(m.group())
            if infos is not None:
                ann = outset.add(m.start(), m.end(), self.ann_type, features=dict(
                    codepoint=infos[0],
                    status=infos[1],
                    emoji=infos[2],
                    name=infos[3],
                    group=infos[4],
                    subgroup=infos[5]
                ))
                if self.string_feature is not None:
                    ann.features[self.string_feature] = doc[ann]
        return doc
