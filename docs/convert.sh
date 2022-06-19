#!/bin/bash

toconvert=$( cat <<EOF
getting-started
EOF
)

for file in $toconvert
do
  echo Converting $file
  jupyter nbconvert -y --execute --to markdown ${file}.ipynb
done
