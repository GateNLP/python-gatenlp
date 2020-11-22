#!/usr/bin/env python
"""
Simple demo implementation for generating HTML Viewer for a bdoc document
"""
import sys
import os
import argparse
from gatenlp import Document

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="input bdoc document")
    parser.add_argument("outfile", help="output html file")
    parser.add_argument(
        "--offline", action="store_true", help="Generate for offline use"
    )
    parser.add_argument(
        "--notebook",
        action="store_true",
        help="Generate for HTML embedding in notebook",
    )
    args = parser.parse_args()

    doc = Document.load(args.infile, fmt="json")
    html = doc.save_mem(
        fmt="html-ann-viewer", offline=args.offline, notebook=args.notebook
    )

    with open(args.outfile, "wt", encoding="utf-8") as outfp:
        outfp.write(html)
