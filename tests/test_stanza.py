import os
from gatenlp import logger, Document


class TestStanza01:
    def test_stanza01a(self):
        try:
            import stanza
            from gatenlp.lib_stanza import stanza2gatenlp, AnnStanza
            from stanza.resources.common import DEFAULT_MODEL_DIR
        except:
            logger.warn("Module stanza not installed, skipping stanza test")
            return
        modelfile = os.path.join(DEFAULT_MODEL_DIR, "en", "default.zip")
        if not os.path.exists(modelfile):
            stanza.download("en")
        nlp = stanza.Pipeline()
        if stanza is None:
            logger.warn("Stanza could not be imported, Stanza tests skipped!")
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
        annstanza = AnnStanza(pipeline=nlp)
        doc = annstanza(doc)
        anns = doc.annset()
        sents = anns.with_type("Sentence")
        assert len(sents) == 2
        tokens = anns.with_type("Token")
        assert len(tokens) == 14


if __name__ == "__main__":
    tests = TestStanza01()
    tests.test_snlp01a()
