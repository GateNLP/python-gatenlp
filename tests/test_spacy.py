import os
from gatenlp import logger, Document


class TestSpacy01:
    def test_spacy01a(self):
        try:
            import spacy
            from gatenlp.lib_spacy import spacy2gatenlp, AnnSpacy
            nlp = spacy.load("en_core_web_sm")
        except:
            logger.warn("Module spacy or model en_core_web_sm not installed, skipping spacy test")
            return
        txt = "Barack Obama was born in Hawaii.  He was elected president in 2008."
        sdoc = nlp(txt)
        gdoc = spacy2gatenlp(sdoc)
        anns = gdoc.annset()
        sents = anns.with_type("Sentence")
        assert len(sents) == 2
        tokens = anns.with_type("Token")
        assert len(tokens) == 14

        annspacy = AnnSpacy(pipeline=nlp)
        doc = Document(txt)
        doc = annspacy(doc)
        anns = doc.annset()
        sents = anns.with_type("Sentence")
        assert len(sents) == 2
        tokens = anns.with_type("Token")
        assert len(tokens) == 14


if __name__ == "__main__":
    tests = TestSpacy01()
    tests.test_spacy01a()
