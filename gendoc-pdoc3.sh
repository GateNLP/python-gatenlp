#!/bin/bash

# NOTE: to avoid import errors the Python package "sphinx" has to be installed in 
# the current conda environment, not just be on the path!
export PYTHONPATH=`pwd`:../python-gatenlp
# NOTE: pdoc3 does not create the html files directly in docs/pythondoc as our sphinx method
# does, but inside a subdirectory gatenlp
pdoc3 gatenlp/ -o docs/pythondoc --html --force
