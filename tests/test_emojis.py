"""
Module for testing the StringGazetteer
"""
import pytest
from gatenlp.document import Document
from gatenlp.processing.emojis import EmojiAnnotator
DOC1_TEXT = "Document contains 🤣 and 🙄, also 💩 and 👍, we also have 👨‍🔧 and 🤛🏻. Variants: 🤚🏽 and 🤚🏾 and 🤚🏿"
DOC2_TEXT = "Newer emojis: 🥲 and 🥸 and 🤌🏿 and 🐻‍❄️ and 🦤 and 🛼 and 😵‍💫 and ❤️‍🩹 and 🧔🏿‍♀️ and 👩🏻‍❤️‍👩🏽 and 🧑🏿‍❤️‍💋‍🧑🏻"


def test_emojisanntr1():
    doc = Document(DOC1_TEXT)
    anntr = EmojiAnnotator()
    doc = anntr(doc)
    anns = list(doc.annset("").with_type("Emoji"))
    assert len(anns) == 9
    assert anns[0].features["name"] == "rolling on the floor laughing"
    assert anns[0].features["subgroup"] == "face-smiling"
    # for ann in anns:
    #     print(f"!!!!!! EMOJI: {ann}")


def test_emojisanntr2():
    doc = Document(DOC2_TEXT)
    anntr = EmojiAnnotator()
    doc = anntr(doc)
    anns = list(doc.annset("").with_type("Emoji"))
    assert len(anns) == 11
    assert anns[0].features["name"] == "smiling face with tear"
    assert anns[0].features["subgroup"] == "face-affection"
    assert anns[10].features["name"] == "kiss: person, person, dark skin tone, light skin tone"
    assert anns[10].features["subgroup"] == "family"
    # for ann in anns:
    #     print(f"!!!!!! EMOJI: {ann}")
