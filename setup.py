#!/usr/bin/env python
# encoding: utf-8
"""Packaging script for the gatenlp library."""
import sys
import os
from setuptools import setup, find_packages
from setup_defs import version, readme, get_install_extras_require, JARFILE_DEST

setup(
    name="gatenlp",
    version=version,
    author="Johann Petrak",
    author_email="johann.petrak@gmail.com",
    url="https://github.com/GateNLP/python-gatenlp",
    keywords=["nlp", "text processing", "natural language processing"],
    description="GATE NLP implementation in Python.",
    long_description=readme,
    long_description_content_type="text/markdown",
    setup_requires=[
        # deliberately not used, since it installs packages without pip,  use the "dev" extras instead
    ],
    install_requires=get_install_extras_require()["base"],
    extras_require=get_install_extras_require(),
    python_requires=">=3.7",
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
            os.path.join("processing", "emojis", "emoji2info.json"),
            os.path.join("processing", "emojis", "emojiregex.txt"),
        ]
    },
    # include_package_data=True,
    # data_files=[("share/gatenlp", [JARFILE_PATH])],
    test_suite="tests",
    entry_points={"console_scripts": [
        "gatenlp-gate-worker=gatenlp.gateworker:run_gate_worker",
        "gatenlp-dir2dir=gatenlp.processing.runners.runner_dir2dir:run_dir2dir",
        "gate_interaction=gatenlp.gate_interaction:main",
    ]},
    classifiers=[
        # "Development Status :: 6 - Mature",
        # "Development Status :: 5 - Production/Stable",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries",
    ],
    project_urls={
        "Documentation": "https://gatenlp.readthedocs.io",
        "Source": "https://github.com/GateNLP/python-gatenlp",
    },
)
