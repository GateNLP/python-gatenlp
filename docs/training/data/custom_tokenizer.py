import re
from gatenlp import GateNlpPr, interact, logger

@GateNlpPr
class MyProcessor:
    def __init__(self):
        self.tokens_total = 0

    def start(self, **kwargs):
        self.tokens_total = 0

    def finish(self, **kwargs):
        logger.info("Total number of tokens: {}".format(self.tokens_total))

    def __call__(self, doc, **kwargs):
        set1 = doc.annset()
        set1.clear()
        text = doc.text
        whitespaces = [m for m in re.finditer(r"[\s,.!?]+|^[\s,.!?]*|[\s,.!?]*$", text)]
        nrtokens = len(whitespaces) - 1
        for k in range(nrtokens):
            fromoff = whitespaces[k].end()
            tooff = whitespaces[k + 1].start()
            set1.add(fromoff, tooff, "Token", {"tokennr": k})
        doc.features["nr_tokens"] = nrtokens
        self.tokens_total += nrtokens

interact()