import os
from gatenlp import logger, Document


class TestSpacy01:

    def test_spacy01a(self):
        """
        Unit test method (make linter happy)
        """
        try:
            import spacy
            from gatenlp.lib_spacy import spacy2gatenlp, AnnSpacy
            nlp = spacy.load("en_core_web_sm")
        except ImportError:
            logger.warning("Module spacy or model en_core_web_sm not installed, skipping spacy test")
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

    def test_spacy02a(self):
        """
        Unit test method (make linter happy)
        """
        try:
            import spacy
            from gatenlp.lib_spacy import spacy2gatenlp, apply_spacy
            nlp = spacy.load("en_core_web_sm")
        except ImportError:
            logger.warning("Module spacy or model en_core_web_sm not installed, skipping spacy test")
            return
        txt = "Barack Obama was born in Hawaii. He was elected president in 2008. "
        doc = Document(txt)
        annset = doc.annset()
        annset.add(0, 32, "Sentence")
        annset.add(33, 67, "Sentence")
        
        anns = doc.annset()
        containing_set1 = anns.with_type("Sentence")
        assert len(containing_set1) == 2
        tokens = anns.with_type("Token")
        assert len(tokens) == 0        
        gdoc = apply_spacy(nlp, doc, setname="spacy1", containing_anns=containing_set1)
      
        annsOut = gdoc.annset("spacy1")
        sents = annsOut.with_type("Sentence")
        assert len(sents) == 2
        tokens = annsOut.with_type("Token")
        assert len(tokens) == 14

        containing_list1 = list(containing_set1)
        gdoc = apply_spacy(nlp, doc, setname="spacy2", containing_anns=containing_list1)
        annsOut = gdoc.annset("spacy2")
        sents = annsOut.with_type("Sentence")
        assert len(sents) == 2
        tokens = annsOut.with_type("Token")
        assert len(tokens) == 14

        containing_list2 = containing_list1[:1]
        assert len(containing_list2) == 1
        gdoc = apply_spacy(nlp, doc, setname="spacy3", containing_anns=containing_list2)
        annsOut = gdoc.annset("spacy3")
        sents = annsOut.with_type("Sentence")
        assert len(sents) == 1
        tokens = annsOut.with_type("Token")
        assert len(tokens) == 7

