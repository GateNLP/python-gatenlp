import inspect
import types
import regex
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
    the types of annotations it creates, and outset_name to identify the output annotation set.

    """

    pass


class NLTKTokenizer(Tokenizer):
    """
    Uses a NLTK Tokenizer to perform tokenization.
    """

    def __init__(
        self, nltk_tokenizer=None, nltk_sent_tokenizer=None, outset_name="", token_type="Token", space_token_type=None
    ):
        """
        Creates the tokenizer. NOTE: this tokenizer does NOT create space tokens by default

        Args:
            nltk_tokenizer: either a class or instance of an nltk tokenizer, or a tokenizer function
                that returns a list of tokens. NOTE: this must be a NLTK tokenizer which supports the
                span_tokenize method or a tokenizer or function that is not destructive, i.e. it must
                be possible to align the created token strings back to the original text. The created
                token strings must not be modified from the original text e.g. " converted to `` or
                similar. For this reason the standard NLTKWordTokenizer cannot be used.
            nltk_sent_tokenizer: some NLTK tokenizers only work correctly if applied to each sentence
                separately after the text is splitted into sentences. This allows to specify an NLTK
                sentence splitter or a sentence splitting function to be run before the word tokenizer.
                Note: if the sentence tokenizer is used the `span_tokenize` method of a tokenizer will
                not be used if it exists, the `tokenize` method will be used.
            outset_name: annotation set to put the Token annotations in
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
            if nltk_sent_tokenizer is not None:
                self.has_span_tokenize = False
            else:
                try:
                    self.tokenizer.span_tokenize("text")
                except Exception as ex:
                    self.has_span_tokenize = False
        self.sent_tokenizer = nltk_sent_tokenizer
        self.sent_is_function = False
        if self.sent_tokenizer and isinstance(self.sent_tokenizer, types.FunctionType):
            self.sent_is_function = True
        self.outset_name = outset_name
        self.token_type = token_type
        self.space_token_type = space_token_type

    def __call__(self, doc, **kwargs):
        if doc.text is None:
            return doc
        if self.has_span_tokenize:
            # this may return a generator, convert to list so we can reuse
            spans = list(self.tokenizer.span_tokenize(doc.text))
        else:
            if self.sent_tokenizer:
                if self.sent_is_function:
                    sents = self.sent_tokenizer(doc.text)
                else:
                    sents = self.sent_tokenizer.tokenize(doc.text)
            else:
                sents = [doc.text]
            print(f"DEBUG: sentences= {sents}")
            if self.is_function:
                tks = [self.tokenizer(s) for s in sents]
            else:
                tks = [self.tokenizer.tokenize(s) for s in sents]
            flat_tks = []
            for tk in tks:
                flat_tks.extend(tk)
            spans = align_tokens(flat_tks, doc.text)
        annset = doc.annset(self.outset_name)
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


class SplitPatternTokenizer(Tokenizer):
    """
    Create annotations for spans of text defined by some literal or regular expression split pattern
    between those spans. Optionally also create annotations for the spans that match the split pattern.
    """
    # TODO: how to properly use type hinting for regex/re patterns?
    def __init__(self,
                 split_pattern: any = regex.compile(r"\s+"),
                 token_pattern: any = None,
                 outset_name: str = "",
                 token_type: str = "Token",
                 space_token_type: str = None):
        """
        Initialize the SplitPatternTokenizer.
        The pattern is either a literal string or a compiled regular expression.

        Args:
            split_pattern: a literal string or a compiled regular expression to find spans which split the text into
                tokens (default: any sequence of one or more whitespace characters)
            token_pattern: if not None, a token annotation is only created if the span between splits (or the begin
                or end of document and a split) matches this pattern: if a literal string, the literal string must
                be present, otherwise must be a compiled regular expression that is found.
            outset_name: the destination annotation set
            token_type: the type of annotation to create for the spans between splits
            space_token_type: if not None, the type of annotation to create for the splits. NOTE: non-splits which
                do not match the token_pattern are not annotated by this!
        """
        self.split_pattern = split_pattern
        self.token_pattern = token_pattern
        self.outset_name = outset_name
        self.token_type = token_type
        self.space_token_type = space_token_type

    def _match_token_pattern(self, text):
        if isinstance(self.token_pattern, str):
            return text.find(self.token_pattern) >= 0
        else:
            return self.token_pattern.search(text)

    def __call__(self, doc, **kwargs):
        annset = doc.annset(self.outset_name)
        last_off = 0
        if isinstance(self.split_pattern, str):
            l = len(self.split_pattern)
            idx = doc.text.find(self.split_pattern)
            while idx > -1:
                if self.space_token_type is not None:
                    annset.add(idx, idx+l, self.space_token_type)
                if idx > last_off:
                    if self.token_pattern is None or (
                            self.token_pattern and self._match_token_pattern(doc.text[last_off:idx])):
                        annset.add(last_off, idx, self.token_type)
                last_off = idx+len(self.split_pattern)
                idx = doc.text.find(self.split_pattern, idx+1)
        else:
            for m in self.split_pattern.finditer(doc.text):
                if self.space_token_type is not None:
                    annset.add(m.start(), m.end(), self.space_token_type)
                if m.start() > last_off:
                    if self.token_pattern is None or (
                            self.token_pattern and self._match_token_pattern(doc.text[last_off:m.start()])):
                        annset.add(last_off, m.start(), self.token_type)
                last_off = m.end()
        if last_off < len(doc.text):
            if self.token_pattern is None or (
                    self.token_pattern and self._match_token_pattern(doc.text[last_off, len(doc.text)])):
                annset.add(last_off, len(doc.text), self.token_type)
        return doc


class ParagraphTokenizer(SplitPatternTokenizer):
    """
    Splits a document into paragraphs, based on the presence of one or more or two or more new lines.
    This is a convenience subclass of SplitPatternTokenizer, for more complex ways to split into paragraphs,
    that class should get used directly.
    """
    def __init__(self, n_nl=1, outset_name="", paragraph_type="Paragraph", split_type=None):
        import re
        nl_str = "\\n" * n_nl
        pat = re.compile(nl_str+"\\n*")
        super().__init__(split_pattern=pat, token_type=paragraph_type, space_token_type=split_type, outset_name=outset_name)

