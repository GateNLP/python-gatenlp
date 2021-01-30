from gatenlp import Document, ChangeLog, GateNlpPr
from gatenlp.gate_interaction import _pr_decorator, DefaultPr, gate_python_plugin_pr


# Simple simulation of the interaction: instead of calling interact() manually call
# the methods from the created wrapper.
class TestInteraction01:
    def test_interaction01_01(self):
        # first: use the DefaultPr
        mypr = _pr_decorator(DefaultPr())
        doc1 = Document("Just a simple document")
        mypr.start({"k1": "v1"})  # set the script parms
        mypr.execute(doc1)
        mypr.finish()

    def test_interaction01_02(self):
        @GateNlpPr
        def do_it(doc: Document, **kwargs):
            set1 = doc.annset("Set1")
            set1.add(2, 3, "test1", {"f1": "value1"})
            # return nothing
        doc1 = Document("Just a simple document")
        doc1.changelog = ChangeLog()
        mypr = gate_python_plugin_pr[0]

        mypr.start({"k1": "v1"})  # set the script parms
        mypr.execute(doc1)
        assert doc1._annotation_sets is not None
        assert len(doc1._annotation_sets) == 1
        assert "Set1" in doc1._annotation_sets
        myset = doc1.annset("Set1")
        assert len(myset) == 1
        myanns = myset.start_ge(0)
        assert len(myanns) == 1
        myann = next(iter(myanns))
        assert myann is not None
        assert myann.start == 2
        assert myann.end == 3
        assert myann.type == "test1"
        # assert myann.id == 1
        assert "f1" in myann.features
        assert myann.features["f1"] == "value1"
        mychlog = doc1.changelog
        assert mychlog is not None
        assert len(mychlog) == 1
        mypr.finish()
