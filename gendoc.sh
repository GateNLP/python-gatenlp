#!/bin/bash

export PYTHONPATH=`pwd`:../python-gatenlp
SPHDIR=./tmp-doc-sphinx
HTMDIR=./tmp-doc-html
rm -rf $SPHDIR
rm -rf $HTMDIR
mkdir $SPHDIR
mkdir $HTMDIR
version=`grep __version__ gatenlp/__init__.py | cut -d" " -f 3-`
sphinx-apidoc -e -f -V $version --ext-autodoc --ext-githubpages -o $SPHDIR gatenlp
mv $SPHDIR/modules.rst $SPHDIR/index.rst
sphinx-build -b html -c sphinx-config $SPHDIR $HTMDIR
cp -r $HTMDIR/* docs/pythondoc/
echo HTML documents have been copied to docs/pythondoc
