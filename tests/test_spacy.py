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

    def test_spacy03(self):
        """
        Unit test method to test data passing between spacy and gate
        """
        try:
            import spacy
            from spacy.language import Language
            from spacy.tokens import Doc
            from spacy.matcher import Matcher
            from gatenlp.lib_spacy import spacy2gatenlp, apply_spacy
            import pkg_resources
            nlp = spacy.load("en_core_web_sm")
        except ImportError:
            logger.warning("Module spacy or model en_core_web_sm not installed, skipping spacy test")
            return
        spv = pkg_resources.parse_version(spacy.__version__)
        if spv < pkg_resources.parse_version("3.0"):
            logger.warning(f"Skipping Spacy test test_spacy03, have version {spacy.__version__} need at least 3.0")
            return
        ## create a language factory
        @Language.factory('number_detector')
        def create_number_detector_component(nlp: Language, name: str):
            return NumberDetector(nlp)

        class NumberDetector(object):

            name = "number_detector"
            matcher: Matcher
            nlp: Language
 
            def __init__(self, nlp: Language):
                # Extensions  include an identifier of the component that creates it, to avoid collisions
                Doc.set_extension("Number_freq",default=False)
                self.nlp = nlp
                self.matcher = Matcher(nlp.vocab)
                pattern = [{'IS_DIGIT': True}]
                
                self.matcher.add("numbers", [pattern], greedy="LONGEST")

            def __call__(self, doc: Doc,number:str,**kwargs) -> Doc:
                # This method is invoked when the component is called on a Doc
                doc._.Number_freq=number
                matches = self.matcher(doc, with_alignments=True)
                refSpans=[]
                for match_id, start, end, matched_list in matches:
                    refSpans.append(doc[start:end])
                    # logging.debug('
                    #     f" matched {self.nlp.vocab[match_id].text} -  { ' '.join( [t.text for t in doc[start:end]])}"
                    #     f"  -- matching {matched_list} -- {ref_set}"
                    # )
                doc.spans["Numbers"]=refSpans
                return doc
        
        
        txt = "When 2 plus 2 makes 5 then  your system is doing something wrong!. " \
              "But in life 2 and 2 not always makes 4. "
        nlp.add_pipe('number_detector')
        doc = Document(txt)
        annset = doc.annset()
        annset.add(0, 66, "Sentence")
        annset.add(67, 106, "Sentence")
        
        anns = doc.annset()
        containing_set1 = anns.with_type("Sentence")
        assert len(containing_set1) == 2
        tokens = anns.with_type("Token")
        assert len(tokens) == 0 
        i = 1
        for ann in containing_set1:
            ann.features["number"] = i
            i += 1
        gdoc = apply_spacy(nlp, doc, setname="spacy1",
                           containing_anns=containing_set1,
                           component_cfg="number_detector",
                           retrieve_spans=["Numbers"])
      
        anns_out = gdoc.annset("spacy1")
        sents = anns_out.with_type("Sentence")
        assert len(sents) == 2
        nums = anns_out.with_type("Numbers")
        assert len(nums) == 6
        for ann in containing_set1:
            assert ann.features["number"] == ann.features["Number_freq"]

