#!/bin/bash

export PYTHONPATH=`pwd`:../python-gatenlp
SPHDIR=./tmp-doc-sphinx
HTMDIR=./tmp-doc-html
rm -rf $SPHDIR
rm -rf $HTMDIR
mkdir $SPHDIR
mkdir $HTMDIR
# cp sphinx-config/index.rst doc-sphinx
sphinx-apidoc -e -f -V "0.1" --ext-autodoc --ext-githubpages -o $SPHDIR gatenlp
mv $SPHDIR/modules.rst $SPHDIR/index.rst
sphinx-build -b html -c sphinx-config $SPHDIR $HTMDIR
cp -r $HTMDIR/* docs/pythondoc/
