master_doc = "index"
project = "GATE NLP library (gatenlp)"
copyright = "2018, University of Sheffield"
author = "Johann Petrak"

# version = '0.1'

html_theme = "classic"
html_theme_options = {"rightsidebar": "false", "relbarbgcolor": "black"}

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

autoclass_content = "both"

# import os
# import sys
# current_dir = os.path.dirname(__file__)
# target_dir = os.path.abspath(os.path.join(current_dir, ".."))
# sys.path.insert(0, target_dir)
# sys.path.insert(0, os.path.join(target_dir,"gatenlp"))
#
# print(target_dir)
