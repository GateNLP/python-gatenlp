"""
Module that provides document source/destination classes for importing and exporting documents
from/to various conll formats.
"""
from gatenlp.utils import stream_from
from gatenlp.corpora import DocumentSource
from conllu import parse, parse_incr


class ConllUFileSource(DocumentSource):
    def __init__(self, source, from_string=False,
                 group_by="doc", n=1,
                 outset="",
                 token_type="Token",
                 mwt_type="MWT",
                 sentence_type="Sentence",
                 add_feats=False,
                 sent_sep="\n",
                 par_sep="\n\n",
                 doc_sep="\n\n\n",
                 ):
        """
        Document source for importing CONLL-U format. Many CONLL-U files do not know about documents
        so documents can be created by reading everything into a single document, creating a document
        per sentence or creating a document per 5 sentences and similar, based on the group_by and n
        settings. For example if group_by="sent" and n=3, a document is created for every 3 sentences.

        NOTE: document name will be set based on the group_by setting and the number of the first
        element the document consists of.

        Args:
            source: a file path or URL if from_string is False, otherwise the CONLL-U string
            from_string: if True, interpret the source as the string input to parse
            group_by: one of "doc" (document), "par" (paragraph) or "sent" (sentence). Together with the
                parameter n influences how gatenlp Document instances are created from the input.
                If the group_by identification "doc" or "par" is not accessible before the first sentence
                of the input, an exception is thrown. Use a very large number to make sure that only a single
                document is created.
            n: the number of group_by elements to include in a document.
            outset: the annotation set name for the annotations to add
            token_type: the type of the token annotations
            mwt_type: the type of multi-word annotations
            sentence_type: if not None, add an annotation covering the sentence and containing any sentence-specific
                meta-data with the given type
            add_feats: if True add document features that give details about what the document contains
            sent_sep: the string to use to separate multiple sentences in a document
            par_sep: the string to use to separate multiple paragraphs in a document
            doc_sep: the string to use to separate multiple conllu docs in a document
        """
        self.source = source
        self.from_string = from_string
        self.group_by = group_by
        self.n = n
        self.outset = outset
        self.token_type = token_type
        self.mwt_type = mwt_type
        self.sentence_type = sentence_type
        self.add_feats = add_feats
        self.sent_sep = sent_sep
        self.par_sep = par_sep
        self.doc_sep = doc_sep

    def tokenlist_generator(self):
        if self.from_string:
            return parse(self.source)
        else:
            with stream_from(self.source) as infp:
                p = parse_incr(infp)
            return p

    def __iter__(self):
        prev_doc = None
        prev_par = None
        n_docs = 0
        n_pars = 0
        n_sents = 0
        n_docs_group = 0
        n_pars_group = 0
        n_sents_group = 0
        perdoc_id2id = {}  # map conll ids to ann ids
        for tl in self.tokenlist_generator():
            meta = tl.metadata
            if meta is None:
                meta = {}
            # check if we have enough sentences, pars, docs to yield a complete document
            # if yes, finish the document, re-initialize the prev_doc/prev_par fields and yield the doc
            # but first check if we got the very first sentence
            if prev_doc is None:  # only None if we are at the very first sentence!
                # make sure we have a doc or par if we are supposed to group by those
                if self.group_by == "doc" and 'newdoc id' not in meta:
                    raise Exception("Cannot group by doc, no newdoc id in the input")
                if self.group_by == "par" and 'newpar id' not in meta:
                    raise Exception("Cannot group by par, no newpar id in the input")
                prev_doc = meta.get("newdoc id", "")
                prev_par = meta.get("newpar id", "")
            elif self.group_by == "sent" and n_sents_group == self.n:
                # we have accumulated enough sentences, yield the document
                pass
            elif self.group_by == "par" and n_pars_group == self.n:
                pass
            elif self.group_by == "sent" and n_sents_group == self.n:
                pass
            # if there is metadata "text" use this as the document text
            # otherwise, construct the document from the tokens (or the MWTs if there are some)
            # we first convert to a list of unattached annotations and incrementally enlarge the text
            # the document is only built once it is complete
