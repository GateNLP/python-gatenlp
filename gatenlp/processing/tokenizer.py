import inspect
from gatenlp.document import Document
from gatenlp.processing.annotator import Annotator

# NOTE we use NLTK's own aligner, but there is also get_original_spans(tk, s) from package tokenizations
from nltk.tokenize.util import align_tokens

# Generate token and optionally space token annotations in the given output annotation set.
# Optionally give non-default type names to the annotations.
# Some tokenizers may also add additional overlapping annotations (e.g. URL, EMAIL) for some tokens
# Tokenizers may have means like lookup tables and patterns for language specific tokenization.
# Tokenizers may have default patterns which work for several languages but should get initialized
# with the language-specific resources in the per-language package.

# in here we could also include pos taggers and lemmatizers as these are related to token features?


class Tokenizer(Annotator):
    """
    A tokenizer creates token annotations and optionally also space token annotations. In additiona it
    may add word annotations for multi-word tokens and and multi-token words.

    Tokenizers should have the fields token_type, space_token_type, and word_type which identify
    the types of annotations it creates, and out_set to identify the output annotation set.

    """

    pass


class NLTKTokenizer(Tokenizer):
    """
    Uses a NLTK Tokenizer to perform tokenization.
    """

    def __init__(
        self, nltk_tokenizer=None, out_set="", token_type="Token", space_token_type=None
    ):
        """
        Creates the tokenizer. NOTE: this tokenizer does NOT create space tokens by default

        Args:
            :param nltk_tokenizer: either a class or instance of an nltk tokenizer
            :param out_set: annotation set to put the Token annotations in
            :param token_type: annotation type of the Token annotations
        """
        assert nltk_tokenizer is not None
        if inspect.isclass(nltk_tokenizer):
            nltk_tokenizer = nltk_tokenizer()
        self.tokenizer = nltk_tokenizer
        # good idea but the method actually exists so instead we call it and if we get
        # an exception (which is a NotImplementedError) we set this to false
        # self.has_span_tokenize = hasattr(nltk_tokenizer, "span_tokenize") and \
        #                         callable(getattr(nltk_tokenizer, "span_tokenize"))
        self.has_span_tokenize = True
        try:
            self.tokenizer.span_tokenize("text")
        except:
            self.has_span_tokenize = False
        self.out_set = out_set
        self.token_type = token_type
        self.space_token_type = space_token_type

    def __call__(self, doc, **kwargs):
        if doc.text is None:
            return doc
        if self.has_span_tokenize:
            spans = self.tokenizer.span_tokenize(doc.text)
        else:
            tks = self.tokenizer.tokenize(doc.text)
            spans = align_tokens(tks, doc.text)
        annset = doc.annset(self.out_set)
        for span in spans:
            annset.add(span[0], span[1], self.token_type)
        return doc
