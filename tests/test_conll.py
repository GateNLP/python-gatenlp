from gatenlp.corpora.conll import ConllUFileSource

txt1 = """
1-2    vámonos   _
1      vamos     ir
2      nos       nosotros
3-4    al        _
3      a         a
4      el        el
5      mar       mar
"""

txt2 = """
1      Sue       Sue
2      likes     like
3      coffee    coffee
4      and       and
5      Bill      Bill
5.1    likes     like
6      tea       tea
"""

txt3 = """
1    Då      då     ADV      AB                    _
2    var     vara   VERB     VB.PRET.ACT           Tense=Past|Voice=Act
3    han     han    PRON     PN.UTR.SIN.DEF.NOM    Case=Nom|Definite=Def|Gender=Com|Number=Sing
4    elva    elva   NUM      RG.NOM                Case=Nom|NumType=Card
5    år      år     NOUN     NN.NEU.PLU.IND.NOM    Case=Nom|Definite=Ind|Gender=Neut|Number=Plur
6    .       .      PUNCT    DL.MAD                _
"""

txt4 = """
1    They     they    PRON    PRP    Case=Nom|Number=Plur               2    nsubj    2:nsubj|4:nsubj
2    buy      buy     VERB    VBP    Number=Plur|Person=3|Tense=Pres    0    root     0:root
3    and      and     CONJ    CC     _                                  4    cc       4:cc
4    sell     sell    VERB    VBP    Number=Plur|Person=3|Tense=Pres    2    conj     0:root|2:conj
5    books    book    NOUN    NNS    Number=Plur                        2    obj      2:obj|4:obj
6    .        .       PUNCT   .      _                                  2    punct    2:punct
"""

txt5 = """
# text = Er arbeitet fürs FBI (deutsch etwa: „Bundesamt für Ermittlung“).
# text_en = He works for the FBI (German approx: “Bundesamt für Ermittlung”).
1     Er           er           PRON    …   _
2     arbeitet     arbeiten     VERB    …   _
3-4   fürs         _            _       …   _
3     für          für          ADP     …   _
4     das          der          DET     …   _
5     FBI          FBI          PROPN   …   _
6     (            (            PUNCT   …   SpaceAfter=No
7     deutsch      deutsch      ADV     …   _
8     etwa         etwa         ADV     …   SpaceAfter=No
9     :            :            PUNCT   …   _
10    „            „            PUNCT   …   SpaceAfter=No
11    Bundesamt    Bundesamt    NOUN    …   _
12    für          für          ADP     …   _
13    Ermittlung   Ermittlung   NOUN    …   SpaceAfter=No
14    “            “            PUNCT   …   SpaceAfter=No
15    )            )            PUNCT   …   SpaceAfter=No
16    .            .            PUNCT   …   _
"""

txt6 = """
# sent_id = 1
# text = They buy and sell books.
1   They     they    PRON    PRP    Case=Nom|Number=Plur               2   nsubj   2:nsubj|4:nsubj   _
2   buy      buy     VERB    VBP    Number=Plur|Person=3|Tense=Pres    0   root    0:root            _
3   and      and     CONJ    CC     _                                  4   cc      4:cc              _
4   sell     sell    VERB    VBP    Number=Plur|Person=3|Tense=Pres    2   conj    0:root|2:conj     _
5   books    book    NOUN    NNS    Number=Plur                        2   obj     2:obj|4:obj       SpaceAfter=No
6   .        .       PUNCT   .      _                                  2   punct   2:punct           _

# sent_id = 2
# text = I have no clue.
1   I       I       PRON    PRP   Case=Nom|Number=Sing|Person=1     2   nsubj   _   _
2   have    have    VERB    VBP   Number=Sing|Person=1|Tense=Pres   0   root    _   _
3   no      no      DET     DT    PronType=Neg                      4   det     _   _
4   clue    clue    NOUN    NN    Number=Sing                       2   obj     _   SpaceAfter=No
5   .       .       PUNCT   .     _                                 2   punct   _   _
"""

txt7 = """
# sent_id = panc0.s4
# text = तत् यथानुश्रूयते।
# translit = tat yathānuśrūyate.
# text_fr = Voilà ce qui nous est parvenu par la tradition orale.
# text_en = This is what is heard.
1     तत्	तद्	DET     _   Case=Nom|…|PronType=Dem   3   nsubj    _   Translit=tat|LTranslit=tad|Gloss=it
2-3   यथानुश्रूयते	_	_       _   _                         _   _        _   SpaceAfter=No
2     यथा	यथा	ADV     _   PronType=Rel              3   advmod   _   Translit=yathā|LTranslit=yathā|Gloss=how
3     अनुश्रूयते   अनु-श्रु	VERB    _   Mood=Ind|…|Voice=Pass     0   root     _   Translit=anuśrūyate|LTranslit=anu-śru|Gloss=it-is-heard
4     ।         ।       PUNCT   _   _                         3   punct    _   Translit=.|LTranslit=.|Gloss=.
"""


class TestConllUSource1:

    def test_conllu_source1_01(self):

        src = ConllUFileSource(txt1, from_string=True)
        ret = list(src)
        assert len(ret) == 1
        doc = ret[0]
        annset = doc.annset()
        assert annset.with_type("MWT").size == 2
        assert annset.with_type("Token").size == 5
        assert src.n_documents == 1

    def test_conllu_source1_02(self):

        src = ConllUFileSource(txt2, from_string=True)
        ret = list(src)
        assert len(ret) == 1
        doc = ret[0]
        annset = doc.annset()
        assert annset.with_type("MWT").size == 0
        assert annset.with_type("Token").size == 7
        assert src.n_documents == 1

    def test_conllu_source1_03(self):

        src = ConllUFileSource(txt3, from_string=True)
        ret = list(src)
        assert len(ret) == 1
        doc = ret[0]
        annset = doc.annset()
        assert annset.with_type("MWT").size == 0
        assert annset.with_type("Token").size == 6
        assert src.n_documents == 1

    def test_conllu_source1_04(self):

        src = ConllUFileSource(txt4, from_string=True)
        ret = list(src)
        assert len(ret) == 1
        doc = ret[0]
        annset = doc.annset()
        assert annset.with_type("MWT").size == 0
        assert annset.with_type("Token").size == 6
        assert src.n_documents == 1

    def test_conllu_source1_05(self):

        src = ConllUFileSource(txt5, from_string=True)
        ret = list(src)
        assert len(ret) == 1
        doc = ret[0]
        annset = doc.annset()
        assert annset.with_type("MWT").size == 1
        assert annset.with_type("Token").size == 16
        assert src.n_documents == 1

    def test_conllu_source1_06(self):

        src = ConllUFileSource(txt6, from_string=True)
        ret = list(src)
        assert len(ret) == 2
        assert src.n_documents == 2
        doc1 = ret[0]
        annset = doc1.annset()
        assert annset.with_type("MWT").size == 0
        assert annset.with_type("Token").size == 6
        doc2 = ret[1]
        annset = doc2.annset()
        assert annset.with_type("MWT").size == 0
        assert annset.with_type("Token").size == 5

    def test_conllu_source1_07(self):

        src = ConllUFileSource(txt7, from_string=True)
        ret = list(src)
        assert len(ret) == 1
        doc = ret[0]
        annset = doc.annset()
        assert annset.with_type("MWT").size == 1
        assert annset.with_type("Token").size == 4
        assert src.n_documents == 1


