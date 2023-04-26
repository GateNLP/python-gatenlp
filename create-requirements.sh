#!/bin/bash

# NOTE: must be run from the root dir of python-gatenlp
# The current environment must include gatenlp[dev]

pipreqs --savepath tmp-requirements.txt --mode gt .
# add packages that we know do not get detected automatically 
echo "pylint" >> tmp-requirements.txt 
echo "pytest-cov" >> tmp-requirements.txt
# comment out pyodide dependency, it causes trouble! 
sed -i -e 's/^pyodide/#pyodide/' tmp-requirements.txt
# create a version that removes stuff not needed for github
# we remove stanza for performance reasons because it pulls in torch
sed -e 's/^ibm/#ibm/' -e 's/^micropip/#micropip/' -e 's/^stanza/#stanza/' tmp-requirements.txt > tmp-requirements-github.txt
pip-compile -r -o tmp-pipcompile.txt --resolver=backtracking tmp-requirements.txt

echo 'Check files:'
echo tmp-requirements.txt
echo tmp-requirements-github.txt
echo tmp-pipcompile.txt

