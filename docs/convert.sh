#!/bin/bash

toconvert=$( cat <<EOF
getting-started
annotations
annotationsets
EOF
)

for file in $toconvert
do
  echo Converting $file
  jupyter nbconvert -y --execute --to markdown ${file}.ipynb
done
