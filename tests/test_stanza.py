from gatenlp.lib_stanza import stanza2gatenlp

try:
    import stanza
    nlp = stanza.Pipeline()
except:
    stanfordnlp = None


class TestStanza01:
    def test_stanza01a(self):
        if stanza is None:
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


if __name__ == "__main__":
    tests = TestStanza01()
    tests.test_snlp01a()