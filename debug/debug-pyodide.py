import micropip
await micropip.install("https://gatenlp.github.io/python-gatenlp/wheels/gatenlp-1.0.8.dev2-py3-none-any.whl")
import gatenlp
from gatenlp.utils import in_notebook, in_colab
from gatenlp import Document
print("In notebook:", in_notebook())
print("In colab:", in_colab())

d1 = Document("This is a document")
d1.annset().add(0,3,"X")
d1
