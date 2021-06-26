import os
import time
from gatenlp import logger, Document


class TestTokenizers01:

    def makedoc(self):
        return Document(" This is a 💩 document.    It has two sentences and 14 tokens. ")

    def test_nltk_tokenizers01(self):
        """
        Unit test method (make linter happy)
        """
        try:
            import nltk
        except ImportError:
            logger.warning("Module nltk not installed, skipping nltk tokenizer test")
            return
        from gatenlp.processing.tokenizer import NLTKTokenizer
        from nltk.tokenize.casual import TweetTokenizer, casual_tokenize
        # Use class
        ntok = NLTKTokenizer(nltk_tokenizer=TweetTokenizer)
        doc = ntok(self.makedoc())
        assert doc.annset().with_type("Token").size == 14
        # same, but also create SpaceToken annotations
        ntok = NLTKTokenizer(nltk_tokenizer=TweetTokenizer, space_token_type="SpaceToken")
        doc = ntok(self.makedoc())
        assert doc.annset().with_type("Token").size == 14
        assert doc.annset().with_type("SpaceToken").size == 13
        # same but specify outset name
        ntok = NLTKTokenizer(nltk_tokenizer=TweetTokenizer, space_token_type="SpaceToken", out_set="OUT")
        doc = ntok(self.makedoc())
        assert doc.annset("OUT").with_type("Token").size == 14
        assert doc.annset("OUT").with_type("SpaceToken").size == 13
        # same but use NLTK tokenizer instance
        ntok = NLTKTokenizer(nltk_tokenizer=TweetTokenizer(), space_token_type="SpaceToken", out_set="OUT")
        doc = ntok(self.makedoc())
        assert doc.annset("OUT").with_type("Token").size == 14
        assert doc.annset("OUT").with_type("SpaceToken").size == 13
        # same but specify convenience function
        ntok = NLTKTokenizer(nltk_tokenizer=casual_tokenize, space_token_type="SpaceToken", out_set="OUT")
        doc = ntok(self.makedoc())
        assert doc.annset("OUT").with_type("Token").size == 14
        assert doc.annset("OUT").with_type("SpaceToken").size == 13

        # regexp
        from nltk.tokenize import RegexpTokenizer
        ntok = NLTKTokenizer(nltk_tokenizer=RegexpTokenizer(r'\w+|\$[\d\.]+|\S+'), space_token_type="SpaceToken")
        doc = ntok(self.makedoc())
        assert doc.annset().with_type("Token").size == 14
        assert doc.annset().with_type("SpaceToken").size == 13

    def test_own_tokenizers(self):
        from gatenlp.processing.tokenizer import SplitPatternTokenizer
        import re

        tok = SplitPatternTokenizer(split_pattern=re.compile(r'\s+'), space_token_type="SpaceToken")
        doc = tok(self.makedoc())
        assert doc.annset().with_type("Token").size == 12   # the dots are not separated from the words
        assert doc.annset().with_type("SpaceToken").size == 13

        tok = SplitPatternTokenizer(
            split_pattern=re.compile(r'\s+'),
            token_pattern=re.compile(r'[a-zA-Z]'),
            space_token_type="SpaceToken")
        doc = tok(self.makedoc())
        assert doc.annset().with_type("Token").size == 10   # also drop the emoji and the number
        assert doc.annset().with_type("SpaceToken").size == 13

        tok = SplitPatternTokenizer(
            split_pattern=" ",
            token_pattern="o",
            space_token_type="SpaceToken")
        doc = tok(self.makedoc())
        assert doc.annset().with_type("Token").size == 3
        assert doc.annset().with_type("SpaceToken").size == 16
