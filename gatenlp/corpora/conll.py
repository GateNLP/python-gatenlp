"""
Module that provides document source/destination classes for importing and exporting documents
from/to various conll formats.
"""
from gatenlp.urlfileutils import stream_from
from gatenlp import Document, AnnotationSet, Span
from gatenlp.corpora import DocumentSource
from conllu import parse, parse_incr


class ConllUFileSource(DocumentSource):
    def __init__(self, source, from_string=False,
                 group_by="sent", n=1,
                 outset="",
                 token_type="Token",
                 mwt_type="MWT",
                 sentence_type="Sentence",
                 add_feats=False,
                 paragraph_type="Paragraph",
                 document_type="Document",
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
            sentence_type: annotation type for the sentence, must be specified
            add_feats: if True add document features that give details about what the document contains
        """
        assert sentence_type is not None
        assert token_type is not None
        assert mwt_type is not None
        self.source = source
        self.from_string = from_string
        self.group_by = group_by
        self.n = n
        self.outset = outset
        self.token_type = token_type
        self.mwt_type = mwt_type
        self.sentence_type = sentence_type
        self.add_feats = add_feats
        self.paragraph_type = paragraph_type
        self.document_type = document_type
        self.n_documents = 0  # gatenlp Documents created
        self.n_conllu_docs = 0  # conllu documents processed
        self.n_conllu_pars = 0  # conllu paragraphs processed
        self.n_conllu_sents = 0  # conllu sentences processed
        self.n_conllu_tokens = 0
        self.n_conllu_mwts = 0

    def gen4list(self, l):
        for el in l:
            yield el

    def tokenlist_generator(self):
        if self.from_string:
            return self.gen4list(parse(self.source))
        else:
            infp = stream_from(self.source)
            p = parse_incr(infp)
            return p

    def tok2features(self, tok):
        """
        Convert a map describing a conllu token, mwt, or empty node to the feature map we want for it.

        Args:
            tok: the token map

        Returns:
            a doctionary to use to create features
        """
        fm = {}
        for k, v in tok.items():
            if k == "form":
                fm["text"] = v
            elif k == "feats":
                if v is not None:
                    fm.update(v)
            elif k == "misc":
                if v is not None:
                    fm.update(v)
            else:
                fm[k] = v
        del fm["id"]
        return fm

    def __iter__(self):
        prev_doc = None
        prev_par = None
        n_docs_group = 0
        n_pars_group = 0
        n_sents_group = 0
        cur_offset = 0
        cur_doc_offset = 0
        cur_par_offset = 0
        have_docids = False
        have_parids = False
        doc = Document("")
        meta = {}
        annset = AnnotationSet()
        reset = False   # after we write a document, this indicates that we need to reset offsets, counts etc
        for tl in self.tokenlist_generator():
            meta = tl.metadata
            if meta is None:
                meta = {}
            # check if we have enough sentences, pars, docs to yield a complete document
            # if yes, finish the document, re-initialize the prev_doc/prev_par fields and yield the doc
            # but first check if we got the very first sentence
            if prev_doc is None:  # only None if we are at the very first sentence!
                # make sure we have a doc or par if we are supposed to group by those
                if 'newdoc id' in meta:
                    have_docids = True
                if 'newpar id' in meta:
                    have_parids = True
                if self.group_by == "doc" and 'newdoc id' not in meta:
                    raise Exception("Cannot group by doc, no newdoc id in the input")
                if self.group_by == "par" and 'newpar id' not in meta:
                    raise Exception("Cannot group by par, no newpar id in the input")
                prev_doc = meta.get("newdoc id", "")
                prev_par = meta.get("newpar id", "")
            elif self.group_by == "sent" and n_sents_group == self.n:
                doc.attach(annset, self.outset)
                yield doc
                self.n_documents += 1
                reset = True
            else:
                docid = meta.get("newdoc id", "")
                parid = meta.get("newpar id", "")
                if docid != "" and docid != prev_doc:
                    annset.add(cur_doc_offset, cur_offset,
                               self.document_type, dict(docid=prev_doc))
                    self.n_conllu_docs += 1
                    n_docs_group += 1
                    prev_doc = docid
                    if self.group_by == "doc" and n_docs_group == self.n:
                        doc.attach(annset, self.outset)
                        yield doc
                        self.n_documents += 1
                        reset = True
                    else:
                        doc._text += "\n\n"
                        cur_offset += 2
                    cur_doc_offset = cur_offset
                if parid != "" and parid != prev_par:
                    annset.add(cur_par_offset, cur_offset,
                               self.paragraph_type, dict(parid=prev_par))
                    self.n_conllu_pars += 1
                    n_pars_group += 1
                    prev_par = parid
                    if not reset and self.group_by == "par" and n_pars_group == self.n:
                        doc.attach(annset, self.outset)
                        yield doc
                        self.n_documents += 1
                        reset = True
                    else:
                        doc._text += "\n"
                        cur_offset += 1
                    cur_par_offset = cur_offset
            if reset:
                doc = Document("")
                annset = AnnotationSet()
                reset = False
                n_docs_group = 0
                n_pars_group = 0
                n_sents_group = 0
                cur_offset = 0
                cur_doc_offset = 0
                cur_par_offset = 0
            else:
                # we process another sentence
                doc._text += "\n"
                cur_offset += 1
            # if there is metadata "text" use this as the document text
            # otherwise, construct the document from the tokens (or the MWTs if there are some)
            # we first convert to a list of unattached annotations and incrementally enlarge the text
            # the document is only built once it is complete
            if "text" in meta:
                havetext = True
                doc._text += meta["text"]
            else:
                havetext = False
            cur_sent_offset = cur_offset
            persent_cid2aid = {}
            persent_anns = []
            tliter = iter(tl)
            for tok in tliter:
                # tok is a map of fields for that token
                # "id" is special as it is the id of the token within a sentence or a token range
                # for MWTs as a tuple (from, "-", to)
                # If the id is a tuple of (id "." subid)
                cid = tok["id"]
                form = tok["form"]
                misc = tok.get("misc")
                if misc is not None:
                    space_after = misc.get("SpaceAfter")
                else:
                    space_after = None
                if isinstance(cid, int):
                    # add annotation for the token
                    if havetext:
                        # match the form in the text
                        cur_offset = doc._text.find(form, cur_offset)
                        if cur_offset < 0:
                            # should not happen, really
                            raise Exception("Could not match token with text")
                    else:
                        doc._text += form
                    # add the token annotation
                    ann = annset.add(cur_offset, cur_offset+len(form), self.token_type, self.tok2features(tok))
                    self.n_conllu_tokens += 1
                    persent_anns.append(ann)
                    persent_cid2aid[cid] = ann.id
                    cur_offset += len(form)
                    if not havetext:
                        # append a space unless we have SpaceAfter=No in field misc
                        if space_after != "No":
                            doc._text += " "
                            cur_offset += 1
                elif cid[1] == "-":
                    # if we get a MWT, we immediately process the individual tokens for the MWT here and add
                    # the annotations for those as well after we add the annotation for the MWT
                    if havetext:
                        # match the form in the text
                        cur_offset = doc._text.find(form, cur_offset)
                        if cur_offset < 0:
                            # should not happen, really
                            raise Exception("Could not match token with text")
                    else:
                        doc._text += form
                    # add the mwt annotation
                    fm = self.tok2features(tok)
                    fm["ids"] = list(range(cid[0], cid[2]+1, 1))
                    ann = annset.add(cur_offset, cur_offset+len(form), self.mwt_type, fm)
                    self.n_conllu_mwts += 1
                    persent_cid2aid[cid] = ann.id
                    persent_anns.append(ann)
                    # handle the tokens
                    ntoks = cid[2] - cid[0] + 1
                    # calculate the spans for the tokens
                    spans = Span.squeeze(cur_offset, cur_offset+len(form), ntoks)
                    for i in range(ntoks):
                        tmptok = next(tliter)
                        ann = annset.add(spans[i].start, spans[i].end, self.token_type, self.tok2features(tmptok))
                        self.n_conllu_tokens += 1
                        persent_cid2aid[tmptok["id"]] = ann.id
                        persent_anns.append(ann)
                    cur_offset += len(form)
                    if not havetext:
                        # append a space unless we have SpaceAfter=No in field misc
                        if space_after != "No":
                            doc._text += " "
                            cur_offset += 1
                elif cid[1] == ".":
                    # if we get an "empty" node we add it as a zero width token annotation to the current offset
                    annset.add(cur_offset-1, cur_offset-1, self.token_type, self.tok2features(tok))
                    self.n_conllu_tokens += 1
            # finished processing all tokens for the sentence
            # add the sentence annotation, unless disabled
            fm = meta
            if "text" in fm:
                del fm["text"]
            ann = annset.add(cur_sent_offset, cur_offset, self.sentence_type, fm)
            n_sents_group += 1
            self.n_conllu_sents += 1
            persent_cid2aid[0] = ann.id
            persent_anns.append(ann)
            # fix up the annotation ids of all annotations we have added for this sentence
            for ann in persent_anns:
                fm = ann.features
                if fm.get("head") is not None:
                    fm["head"] = persent_cid2aid[fm["head"]]
                elif fm.get("ids") is not None:
                    fm["ids"] = [persent_cid2aid[x] for x in fm["ids"]]
                elif fm.get("deps") is not None:
                    fm["deps"] = [persent_cid2aid[x] for x in fm["deps"]]
        if len(doc.text) > 0:
            docid = meta.get("newdoc id", "")
            parid = meta.get("newpar id", "")
            if have_docids:
                annset.add(cur_doc_offset, cur_offset, self.document_type,
                           dict(docid=prev_doc))
                self.n_conllu_docs += 1
            if have_parids:
                annset.add(cur_doc_offset, cur_offset, self.paragraph_type,
                           dict(parid=prev_par))
                self.n_conllu_pars += 1
            doc.attach(annset, self.outset)
            yield doc
            self.n_documents += 1