#!/usr/bin/env python
# encoding: utf-8

"""Packaging script for the gatenlp library."""
import sys
import os
import subprocess
from setuptools import setup, find_packages
import re
from shutil import copyfile

JARFILE = "gatetools-gatenlpslave-1.0.jar"
JARFILE_PATH = os.path.join("java","target", JARFILE) # where it is after compiling
JARFILE_DIST = os.path.join("gatenlp", "_jars", JARFILE) # where to put the jarfile prior before running setup
JARFILE_DEST = os.path.join("_jars", JARFILE) # where it should be relative to the gatenlp package
JAVAFILE_PATH = os.path.join("java", "src", "main", "java", "gate", "tools", "gatenlpslave", "GatenlpSlave.java")

HTML_ANN_VIEWER_HTML_FILE = os.path.join("html-ann-viewer", "gatenlp-ann-viewer.html")
HTML_ANN_VIEWER_MERGEDJS_FILE = os.path.join("html-ann-viewer", "gatenlp-ann-viewer-merged.js")
HTML_ANN_VIEWER_GATEJS_FILE = os.path.join("html-ann-viewer", "gatenlp-ann-viewer.js")
HTML_ANN_VIEWER_LIBJS_FILE = os.path.join("html-ann-viewer", "jquery-3.5.1.min.js")
HTML_ANN_VIEWER_DIST_DIR = os.path.join("gatenlp", "serialization", "_htmlviewer")

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    readme = f.read()


def versionfromfile(*filepath):
    here = os.path.abspath(os.path.dirname(__file__))
    infile = os.path.join(here, *filepath)
    with open(infile) as fp:
        version_match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]",
                                  fp.read(), re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string in {}.".format(infile))


def make_java():
    if os.path.exists(JARFILE_DIST) and os.stat(JARFILE_DIST).st_mtime > os.stat(JAVAFILE_PATH).st_mtime:
        return
    os.chdir("java")
    retcode = subprocess.call("mvn package", shell=True)
    if retcode != 0:
        raise Exception("Could not build jar, exit code is {}".format(retcode))
    os.chdir("..")
    copyfile(JARFILE_PATH, JARFILE_DIST)


def make_html_ann_viewer():
    # concatenate the JS files to create the merged file
    with open(HTML_ANN_VIEWER_MERGEDJS_FILE, "wt", encoding="UTF-8") as outfp:
        for fname in [HTML_ANN_VIEWER_LIBJS_FILE, HTML_ANN_VIEWER_GATEJS_FILE]:
            with open(fname, "rt", encoding="UTF-8") as infp:
                for line in infp:
                    outfp.write(line)
    print("Copying HTML and merged JS files", file=sys.stderr)
    copyfile(HTML_ANN_VIEWER_HTML_FILE, os.path.join(HTML_ANN_VIEWER_DIST_DIR, "gatenlp-ann-viewer.html"))
    copyfile(HTML_ANN_VIEWER_MERGEDJS_FILE, os.path.join(HTML_ANN_VIEWER_DIST_DIR, "gatenlp-ann-viewer-merged.js"))

version=versionfromfile("gatenlp/__init__.py")

make_html_ann_viewer()

make_java()


def get_install_extras_require():
    extras_require = {
        'formats': ['msgpack', 'pyyaml', 'bs4', 'requests'],
        'java': ['py4j'],
        'stanza': ['stanza'],
        'spacy': ['spacy'],
        'nltk': ['nltk'],
        'stanfordnlp': ['stanfordnlp'],
        'gazetteers': ['matchtext'],
        # the following are not included in all:
        'dev': ['pytest', 'pytest-pep8', 'pytest-cov', 'pytest-runner', 'sphinx', 'pdoc3'],  # for development
    }
    # Add automatically the 'all' target
    extras_require.update({'all': [i[0] for i in extras_require.values() if i[0] not in ['dev']]})
    return extras_require

setup(
    name="gatenlp",
    version=version,
    author="Johann Petrak",
    author_email="johann.petrak@gmail.com",
    url='https://github.com/GateNLP/python-gatenlp',
    keywords=['nlp', 'text processing'],
    description='GATE NLP implementation in Python.',
    long_description=readme,
    long_description_content_type='text/markdown',
    setup_requires=[
        "pytest-runner",
        "pygit2",
        # TODO: figure those out:
        #"setuptools_git",
        #"setuptools_scm", 
        ],
    install_requires=[
      'sortedcontainers>=2.0.0',
    ],
    extras_require=get_install_extras_require(),
    python_requires=">=3.5",
    tests_require=['pytest'],
    platforms='any',
    license="MIT",
    packages=find_packages(),
    package_data={"gatenlp": [JARFILE_DEST]},  
    # include_package_data=True,
    # data_files=[("share/gatenlp", [JARFILE_PATH])],
    test_suite='tests',
    entry_points={"console_scripts": ["gatenlp-gate-slave=gatenlp.gateslave:main"]},
    classifiers=[
        # "Development Status :: 6 - Mature",
        # "Development Status :: 5 - Production/Stable",
        "Development Status :: 4 - Beta",
        # "Development Status :: 3 - Alpha",
        # "Development Status :: 2 - Pre-Alpha",
        # "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
      ],
    )


