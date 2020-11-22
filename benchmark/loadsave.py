import gatenlp
from gatenlp.docformats import simplejson
import time
import datetime
import sys
import os.path
import glob

# NOTE: maybe analyse with python profiling

_, inpat, outdir = sys.argv

infiles = glob.glob(inpat)
print("Number of input files:", len(infiles), file=sys.stderr)

if not os.path.exists(outdir):
    raise Exception("Does not exist: {}".format(outdir))
if not os.path.isdir(outdir):
    raise Exception("Not a directory: {}".format(outdir))

start = time.time()
docs = []
for f in infiles:
    with open(f, "rt", encoding="utf-8") as fp:
        doc = simplejson.load(fp)
        docs.append(doc)
stop = time.time()
elapsed = stop - start
print(
    "Elapsed time for loading: {} / {}".format(
        elapsed, datetime.timedelta(seconds=elapsed)
    )
)

start = time.time()
for doc in docs:
    with open(f, "wt", encoding="utf-8") as fp:
        simplejson.dump(doc, fp)
stop = time.time()
elapsed = stop - start
print(
    "Elapsed time for saving: {} / {}".format(
        elapsed, datetime.timedelta(seconds=elapsed)
    )
)
