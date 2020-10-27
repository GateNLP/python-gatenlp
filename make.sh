#!/bin/bash

set -e

python make-viewer.py
python make-java.py
python setup.py "$@" 
coverage html
