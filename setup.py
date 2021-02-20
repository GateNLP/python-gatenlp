#!/usr/bin/env python
# encoding: utf-8

"""Packaging script for the gatenlp library."""
import sys
import os
from setuptools import setup, find_packages
import re

if sys.version_info < (3, 6):
    sys.exit("ERROR: gatenlp requires Python 3.6+")

JARFILE = "gatetools-gatenlpworker-1.0.jar"
JARFILE_DEST = os.path.join(
    "_jars", JARFILE
)  # where it should be relative to the gatenlp package


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md")) as f:
    readme = f.read()


def versionfromfile(*filepath):
    here = os.path.abspath(os.path.dirname(__file__))
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
        "formats": ["msgpack", "pyyaml", "beautifulsoup4>=4.9.3", "requests", "conllu"],
        "java": ["py4j"],
        "stanza": ["stanza>=1.2"],
        "spacy": ["spacy>=2.3"],
        "nltk": ["nltk>=3.5"],
        "notebook": [
            "ipython",
            "ipykernel",
            "jupyterlab",
            "notebook",
            "voila",
            "RISE",
            "ipywidgets",
        ],
        "gazetteers": ["matchtext", "recordclass"],
        # the following are not included in all but in alldev
        "dev": [
            "pytest",
            "pytest-pep8",
            "pytest-cov",
            "pytest-runner",
            "sphinx",
            "pdoc3",
            "tox",
            "mypy",
            "pytest-tornasync",  # TODO: have to figure out why we need this? Maybe because we added jupyterlab,notebook,voila
            "black[d]",  # for automatic code formatting
        ],
    }
    # Add automatically the 'all' target
    add_all = [p for l in extras_require.values() for p in l if p not in ["dev"]]
    add_alldev = [p for l in extras_require.values() for p in l]
    extras_require.update({"all": add_all, "alldev": add_alldev})
    return extras_require


setup(
    name="gatenlp",
    version=version,
    author="Johann Petrak",
    author_email="johann.petrak@gmail.com",
    url="https://github.com/GateNLP/python-gatenlp",
    keywords=["nlp", "text processing"],
    description="GATE NLP implementation in Python.",
    long_description=readme,
    long_description_content_type="text/markdown",
    setup_requires=[
        # deliberately not used, since it installs packages without pip,  use the "dev" extras instead
    ],
    install_requires=[
        "sortedcontainers>=2.0.0",
    ],
    extras_require=get_install_extras_require(),
    # NOTE: this is not actually used since it will not work with gatenlp version reporting
    # from the gateplugin-Python plugin (since _version.py is not/should not get committed, only distributed)
    # (this would also not work if we deploy after committing)
    python_requires=">=3.6",
    tests_require=["pytest", "pytest-cov"],
    platforms="any",
    license="Apache License 2.0",
    packages=find_packages(),
    package_data={
        "gatenlp": [
            JARFILE_DEST,
            os.path.join("serialization", "_htmlviewer", "gatenlp-ann-viewer.html"),
            os.path.join(
                "serialization", "_htmlviewer", "gatenlp-ann-viewer-merged.js"
            ),
        ]
    },
    # include_package_data=True,
    # data_files=[("share/gatenlp", [JARFILE_PATH])],
    test_suite="tests",
    entry_points={"console_scripts": ["gatenlp-gate-worker=gatenlp.gateworker:main"]},
    classifiers=[
        # "Development Status :: 6 - Mature",
        # "Development Status :: 5 - Production/Stable",
        "Development Status :: 4 - Beta",
        # "Development Status :: 3 - Alpha",
        # "Development Status :: 2 - Pre-Alpha",
        # "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: Apache Software License",
    ],
)
