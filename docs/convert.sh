

# Note: the following files must get converted manually because they depend on 
# authentication or cannot be fully automated for other reasons:
# client_elg: needs interactive authentication
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
client_googlenlp
client_rewire
client_perspective
processing
tokenizers
gazetteers
stringregex
pampac
EOF
)

toconvert2=$( cat <<EOF
visualization
corpora
EOF
)

for file in $toconvert
do
  echo Converting $file to Markdown
  jupyter nbconvert -y --execute --to markdown ${file}.ipynb
done

for file in $toconvert2
do
  echo Converting $file via HTML to Markdown
  jupyter nbconvert -y --execute --to html ${file}.ipynb
  tail +3 ${file}.html  | sed -e 's/<head>/<div>/' -e 's/<\/head>//' -e 's/<body>//' -e 's/<\/body>//' -e 's/<\/html>//' > ${file}.md
  rm ${file}.html
done
