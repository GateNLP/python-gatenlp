#!/bin/bash

# Note: the following files must get converted manually because they depend on 
# authentication or cannot be fully automated for other reasons:
# client_elg
# gateworker: start the PythonWorkerLr in GATE gui on default port,
#    run: gatenlp-gate-worker --port 31333 --auth even-more-secret
toconvert=$( cat <<EOF
getting-started
annotations
annotationsets
documents
changelogs
lib_spacy
lib_stanza
client_gatecloud
client_ibmnlu
client_tagme
client_textrazor
EOF
)

for file in $toconvert
do
  echo Converting $file
  jupyter nbconvert -y --execute --to markdown ${file}.ipynb
done
