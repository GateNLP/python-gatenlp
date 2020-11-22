#!/usr/bin/env python
# encoding: utf-8

"""Packaging script for the gatenlp library."""
import sys
import os
import subprocess
from setuptools import setup, find_packages
import re
from shutil import copyfile

HTML_ANN_VIEWER_HTML_FILE = os.path.join("html-ann-viewer", "gatenlp-ann-viewer.html")
HTML_ANN_VIEWER_MERGEDJS_FILE = os.path.join(
    "html-ann-viewer", "gatenlp-ann-viewer-merged.js"
)
HTML_ANN_VIEWER_GATEJS_FILE = os.path.join("html-ann-viewer", "gatenlp-ann-viewer.js")
HTML_ANN_VIEWER_LIBJS_FILE = os.path.join("html-ann-viewer", "jquery-3.5.1.min.js")
HTML_ANN_VIEWER_DIST_DIR = os.path.join("gatenlp", "serialization", "_htmlviewer")

here = os.path.abspath(os.path.dirname(__file__))


def make_html_ann_viewer():
    # concatenate the JS files to create the merged file
    with open(HTML_ANN_VIEWER_MERGEDJS_FILE, "wt", encoding="UTF-8") as outfp:
        for fname in [HTML_ANN_VIEWER_LIBJS_FILE, HTML_ANN_VIEWER_GATEJS_FILE]:
            with open(fname, "rt", encoding="UTF-8") as infp:
                for line in infp:
                    outfp.write(line)
    print("Copying HTML and merged JS files", file=sys.stderr)
    copyfile(
        HTML_ANN_VIEWER_HTML_FILE,
        os.path.join(HTML_ANN_VIEWER_DIST_DIR, "gatenlp-ann-viewer.html"),
    )
    copyfile(
        HTML_ANN_VIEWER_MERGEDJS_FILE,
        os.path.join(HTML_ANN_VIEWER_DIST_DIR, "gatenlp-ann-viewer-merged.js"),
    )


make_html_ann_viewer()
