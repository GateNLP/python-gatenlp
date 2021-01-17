#!/usr/bin/env python

import gatenlp
from gatenlp import Document
import time
import argparse
import datetime
import os.path
from pathlib import Path
from gatenlp.utils import init_logger, run_start, run_stop

# NOTE: maybe analyse with python profiling

def process_args(args=None):
    parser = argparse.ArgumentParser(
        description = """
        Benchmark the performance of loading and saving files in various serialization formats.
        """
    )
    parser.add_argument("indir", type=str,
                        help="Directory where to read the initial files from")
    parser.add_argument("outdir", type=str,
                        help="Directory where to save and load using the benchmark format")
    parser.add_argument("--infmt", type=str, default="bdocjs",
                        help="Format / extension of initial files")
    parser.add_argument("--fmt", type=str, default="bdocjs",
                        help="Format / extension of benchmark files")
    args = parser.parse_args(args)
    return args


if __name__ == "__main__":

    args = process_args()
    logger = init_logger("loadsave")
    run_start(logger, "loadsave")

    if not os.path.exists(args.indir):
        raise Exception("Does not exist: {}".format(args.indir))
    if not os.path.exists(args.outdir):
        raise Exception("Does not exist: {}".format(args.outdir))

    gen = Path(args.indir).rglob("*.bdocjs")

    total_readorig = 0
    total_save = 0
    total_read = 0
    newfiles = []
    for f in gen:
        relpath = str(f)
        start = time.time()
        doc = Document.load(relpath, fmt=args.infmt)
        total_readorig += time.time() - start
        relpath = relpath.replace(os.path.sep, "_")
        relpath = relpath.replace(".bdocjs", args.fmt)
        newfile = os.path.join(args.outdir, relpath)
        newfiles.append(newfile)
        start = time.time()
        doc.save(newfile, fmt=args.fmt)
        total_save += time.time() - start

    for f in newfiles:
        start = time.time()
        doc = Document.load(f, fmt=args.fmt)
        total_read += time.time() - start

    n = len(newfiles)
    avg_readorig = total_readorig / n
    avg_read = total_read / n
    avg_save = total_save / n
    logger.info(f"Number of files processed: {len(newfiles)}")
    logger.info(f"Average time (secs) reading origs: {avg_readorig}")
    logger.info(f"Average time (secs) reading fmt:   {avg_read}")
    logger.info(f"Average time (secs) writing fmt:   {avg_save}")
