import inspect
import types
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
            nltk_tokenizer: either a class or instance of an nltk tokenizer, or a tokenizer function
                that returns a list of tokens
            out_set: annotation set to put the Token annotations in
            token_type: annotation type of the Token annotations
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
        self.is_function = False
        if isinstance(self.tokenizer, types.FunctionType):
            self.has_span_tokenize = False
            self.is_function = True
        else:
            try:
                self.tokenizer.span_tokenize("text")
            except Exception as ex:
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
            if self.is_function:
                tks = self.tokenizer(doc.text)
            else:
                tks = self.tokenizer.tokenize(doc.text)
            spans = align_tokens(tks, doc.text)
        annset = doc.annset(self.out_set)
        for span in spans:
            annset.add(span[0], span[1], self.token_type)
        if self.space_token_type is not None:
            last_off = 0
            for span in spans:
                if span[0] > last_off:
                    annset.add(last_off, span[0], self.space_token_type)
                    last_off = span[1]
                else:
                    last_off = span[1]
            if last_off < len(doc.text):
                annset.add(last_off, len(doc.text), self.space_token_type)
        return doc
