#!/usr/bin/env python
# encoding: utf-8
"""Definitions and methos used by setup.py and other build-related programs."""

import sys
import os
import re


if sys.version_info < (3, 7):
    sys.exit("ERROR: gatenlp requires Python 3.7+")

JARFILE = "gatetools-gatenlpworker-1.0.jar"
JARFILE_DEST = os.path.join(
    "_jars", JARFILE
)  # where it should be relative to the gatenlp package


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md")) as f:
    readme = f.read()


def versionfromfile(*filepath):
    infile = os.path.join(here, *filepath)
    with open(infile) as fp:
        version_match = re.search(
            r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", fp.read(), re.M
        )
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string in {}.".format(infile))


version = versionfromfile("gatenlp/version.py")


def get_install_extras_require():
    extras_require = {
        "base": ["sortedcontainers>=2.0.0", "iobes"],
        "clientibm": ["ibm-watson"],
        "clientelg": ["requests", "elg"],
        "clienttagme": ["requests"],
        "clienttextrazor": ["requests"],
        "clientgatecloud": ["requests"],
        "clientgooglenlp": ["google-cloud-language"],
        "clientperspective": ["google-api-python-client"],
        "clients": ["requests", "elg", "ibm-watson", "google-cloud-language", "google-api-python-client"],
        "formats": ["msgpack", "pyyaml>=5.2", "beautifulsoup4>=4.9.3", "requests", "conllu", "iobes", ],
        "java": ["py4j", "requests"],
        "stanza": ["stanza>=1.3.0"],
        "spacy": ["spacy>=2.2"],
        "nltk": ["nltk>=3.5"],
        "mltner": ["tner"],
        # the following are not included in all but in alldev
        "notebook": [
            "ipython",
            "ipykernel",
            "jupyterlab",
            "notebook",
            "voila",
            "RISE",
            "ipywidgets",
        ],
        "ray": ["ray[default]"],
        "dev": [
            "pytest",
            "pytest-pep8",
            "pytest-cov",
            "pytest-runner",
            "sphinx",
            "pdoc3",
            "tox",
            "mypy",
            "bandit",
            "prospector[with_pyroma,with_vulture,with_mypy,with_bandid,with_frosted]",
            # TODO: have to figure out why we need this? Maybe because we added jupyterlab,notebook,voila
            "pytest-tornasync",
            "flake8",
            "black[d]",  # for automatic code formatting
            "pipreqs",   # for dealing with requirements/dependencies
            "pip-tools", # for dealing with requirements/dependencies
        ],
        "github": [
            "flake8",
            "pytest",
            "pytest-cov",
            "pytest-pep8"
        ]
    }
    pck_all = set()
    pck_alldev = set()
    # NOTE: getting installation problems with tner, excluding mltner until resolved
    for name, pcks in extras_require.items():
        if name not in ["dev", "notebook", "github", "mltner"]:
            pck_all.update(pcks)
        if name not in ["github", "mltner"]:
            pck_alldev.update(pcks)
    pck_all = sorted(list(pck_all))
    pck_alldev = sorted(list(pck_alldev))
    extras_require.update({"all": pck_all, "alldev": pck_alldev})
    return extras_require


