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
if [[ x"$1" == x ]]
then
  python setup.py test |& tee -a make.log
else
  python setup.py "$@"  |& tee -a make.log
fi
pytest --cov=gatenlp
coverage report -i |& tee -a make.log
coverage html -i
