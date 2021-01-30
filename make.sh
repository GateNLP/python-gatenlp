#!/bin/bash

set -e
touch make.log
rm make.log
python make-viewer.py |& tee -a make.log
python make-java.py |& tee -a make.log
pycodestyle gatenlp |& tee -a make.log
flake8 gatenlp |& tee -a make.log
pylint gatenlp |& tee -a make.log
pyflakes gatenlp |& tee -a make.log
python setup.py "$@"  |& tee -a make.log
coverage report |& tee -a make.log
coverage html 
