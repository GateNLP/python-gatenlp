#!/usr/bin/env python
# encoding: utf-8

"""Packaging script for the gatenlp library."""

import os
from setuptools import setup, find_packages
import re

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

setup(
    name="gatenlp",
    version=versionfromfile("gatenlp/__init__.py"),
    author="Johann Petrak",
    author_email="johann.petrak@gmail.com",
    description='Library for GATE NLP interaction and resource manipulation',
    long_description=readme,
    long_description_content_type='text/markdown',
    setup_requires=["pytest-runner"],
    install_requires=["sortedcontainers"],
    python_requires=">=3.6",
    tests_require=['pytest'],
    platforms='any',
    license="MIT",
    keywords="",
    url="https://github.com/GateNLP/python-gatenlp",
    packages=find_packages(),
    test_suite='tests',
    classifiers=[
        # "Development Status :: 6 - Mature",
        # "Development Status :: 5 - Production/Stable",
        # "Development Status :: 4 - Beta",
        # "Development Status :: 3 - Alpha",
        "Development Status :: 2 - Pre-Alpha",
        # "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
      ],
)

