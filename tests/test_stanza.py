import os
import time
from gatenlp import logger, Document


class TestStanza01:

    def test_stanza01a(self):
        """
        Unit test method (make linter happy)
        """
        try:
            import stanza
            from gatenlp.lib_stanza import stanza2gatenlp, AnnStanza
            from stanza.resources.common import DEFAULT_MODEL_DIR
        except ImportError:
            logger.warning("Module stanza not installed, skipping stanza test")
            return
        modelfile = os.path.join(DEFAULT_MODEL_DIR, "en", "default.zip")
        if not os.path.exists(modelfile):
            stanza.download("en")
        nlp = stanza.Pipeline(use_gpu=False)
        if stanza is None:
            logger.warning("Stanza could not be imported, Stanza tests skipped!")
            return
        txt = "Barack Obama was born in Hawaii.  He was elected president in 2008."
        sdoc = nlp(txt)
        gdoc = stanza2gatenlp(sdoc)
        anns = gdoc.annset()
        sents = anns.with_type("Sentence")
        assert len(sents) == 2
        # words = anns.with_type("Word")
        # assert len(words) == 14
        tokens = anns.with_type("Token")
        assert len(tokens) == 14

        doc = Document(txt)
        annstanza = AnnStanza(pipeline=nlp, batchsize=50)
        doc = annstanza(doc)
        anns = doc.annset()
        sents = anns.with_type("Sentence")
        assert len(sents) == 2
        tokens = anns.with_type("Token")
        assert len(tokens) == 14

        # test Stanza batching and check speed improvement
        nlp = stanza.Pipeline(use_gpu=False, processors="tokenize")
        annstanza = AnnStanza(pipeline=nlp)
        docs_p = []
        docs_c = []
        for i in range(103):
            docs_p.append(Document(txt))
            docs_c.append(Document(txt))
        time_pipe = time.perf_counter()
        docs_processed_pipe = list(annstanza.pipe(docs_p))
        time_pipe = time.perf_counter() - time_pipe
        docs_processed_call = []
        time_call = time.perf_counter()
        for doc in docs_c:
            docs_processed_call.append(annstanza(doc))
        time_call = time.perf_counter() - time_call
        # print(f"!!!!!!! PIPE={time_pipe}, CALL={time_call}, speedup is {time_call/time_pipe}")
        # assert time_call > time_pipe
        # check equality of both lists of processed documents by first converting to dicts
        assert len(docs_p) == len(docs_processed_pipe)
        assert len(docs_processed_call) == len(docs_processed_pipe)
        d_pipe = docs_processed_pipe[0]
        d_call = docs_processed_call[0]
        assert d_pipe.text == d_call.text
        assert d_pipe.annset_names() == d_call.annset_names()
        for n in d_pipe.annset_names():
            as_p = d_pipe.annset(n)
            as_c = d_call.annset(n)
            assert as_p.size == as_c.size
            for ap, ac in zip(as_p, as_c):
                assert ap.equal(ac)
        d_pipe_d = d_pipe.to_dict()
        d_call_d = d_call.to_dict()
        assert d_pipe_d == d_call_d
