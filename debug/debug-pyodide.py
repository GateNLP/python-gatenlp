import micropip
await micropip.install("https://gatenlp.github.io/python-gatenlp/wheels/gatenlp-1.0.8.dev2-py3-none-any.whl")
import gatenlp
from gatenlp import Document

d1 = Document("This is a document")
d1.annset().add(0,3,"X")
d1
