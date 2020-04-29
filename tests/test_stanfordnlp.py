from gatenlp.lib_stanfordnlp import stanfordnlp2gatenlp

try:
    import stanfordnlp
    nlp = stanfordnlp.Pipeline()
except:
    stanfordnlp = None

class TestStanfordNlp01:
    def test_snlp01a(self):
        if stanfordnlp is None:
            return
        txt = "Barack Obama was born in Hawaii.  He was elected president in 2008."
        sdoc = nlp(txt)
        gdoc = stanfordnlp2gatenlp(sdoc)
        anns = gdoc.get_annotations()
        sents = anns.with_type("Sentence")
        assert len(sents) == 2
        words = anns.with_type("Word")
        assert len(words) == 14


if __name__ == "__main__":
    tests = TestStanfordNlp01()
    tests.test_snlp01a()