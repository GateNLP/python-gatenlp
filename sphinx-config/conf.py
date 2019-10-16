master_doc = 'index'
project = 'GATE NLP library (gatenlp)'
copyright = '2018, University of Sheffield'
author = 'Johann Petrak'

# version = '0.1'

html_theme = "classic"
html_theme_options = {
    "rightsidebar": "false",
    "relbarbgcolor": "black"
}

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

