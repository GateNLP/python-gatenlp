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
        ann = annset.add(0,32 ,"Sentence",{})
        ann = annset.add(33,67,"Sentence",{})
        
        anns = doc.annset()
        sents = anns.with_type("Sentence")
        assert len(sents) == 2
        tokens = anns.with_type("Token")
        assert len(tokens) == 0        
        gdoc=apply_spacy(nlp,doc , setname="spacy", containing_anns=anns)
      
        annsOut = gdoc.annset("spacy")
        sents = annsOut.with_type("Sentence")
        assert len(sents) == 2
        tokens = annsOut.with_type("Token")
        assert len(tokens) == 14
 
 
