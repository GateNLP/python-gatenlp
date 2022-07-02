# Installation

Make sure you have Python 3.7 or later installed.

The recommended way to install Python is to use Conda by installing  one of 

* [Anaconda](https://www.anaconda.com/products/individual) or
* [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 

Alternately, 
* [Miniforge](https://github.com/conda-forge/miniforge) may help avoid Windows 10 issues


Then create an environment for working with gatenlp. This example
creates an environment with the name `gatenlp`, python 3.8 and activates it:

```
conda create -n gatenlp python==3.8
conda activate gatenlp
```

Note that the `gatenlp` package is compatible with several of the most recent Python 
versions: the most recent version is compatible with: [![Python compatibility](https://img.shields.io/pypi/pyversions/gatenlp.svg)](https://pypi.python.org/pypi/gatenlp/)

The gatenlp has a number of optional dependencies which are only needed if
some special features of gatenlp are used.

To install `gatenlp` with the minimal set of dependencies run:

```
python -m pip install gatenlp 
```

To upgrade an already installed gatenlp package to the latest version run: 

```
python -m pip install -U gatenlp 
```

To install `gatenlp` with all dependencies run:

```
python -m pip install gatenlp[all,notebook]
```

To upgrade to the latest version with all dependencies:

```
python -m pip install  -U gatenlp[all,notebook]
```

To upgrade or install to the latest version, INCLUDING pre-release, alpha, or beta versions, use:

```
python -m pip install --pre -U gatenlp[all,notebook]
```

NOTE: if this fails because of a problem installing torch (this may happen on Windows), 
first install Pytorch separately according to 
the Pytorch installation instructions, see: https://pytorch.org/get-started/locally/
then run the gatenlp installation again. 

The following specific dependencies included in 'all' can be chosen separately:
* `formats`: to support the various serialization formats
* `java`: to support the Gate worker
* `stanza`: to support the Stanza bridge
* `spacy`: to support the Spacy bridge
* `nltk`: to support the nltk tokenizer and nltk bridge
* `clients`: to support using gatenlp as a client for ELG services, Google NLP, IBM Watson, TextRazor, GATE Cloud
* `ray`: to run multiprocessing pipelines using Ray

The following dependencies are not included in 'all' but in 'alldev' or can be chosen separately:
* `notebook`: needed to use `gatenlp` with notebooks, convert notebooks, show notebooks as slides 
* `dev`: dependencies needed for developing gatenlp, testing, linting etc. 

Example: to install gatenlp with support for stanza and spacy and serialization:

```
python -m pip install gatenlp[stanza,spacy,formats]
```


To install the latest `gatenlp` code from GitHub with all dependencies:
* Clone the repository and change into it
* Run `python -m pip install -e .[all]`

To also install everything needed for development use "alldev":

```
python -m pip install -e .[alldev]
```

#### Creating a jupyter notebook/lab kernel:

To use the conda environment with jupyter notebook/lab create kernel:

* activate the environment
* run `python -m ipykernel install --user --name=gatenlp` 
  (or choose a different name in place of "gatenlp" for the kernel)
* this kernel should then show up in the list of kernels within jupyter notebook or lab

#### Installing directly from GitHub

To install directly from the current GitHub main branch:

```
python -m pip install https://github.com/GateNLP/python-gatenlp.git
```

To also specify extras:

```
python -m pip install https://github.com/GateNLP/python-gatenlp.git#egg=gatenlp[stanza]
```

To install a specific branch, tag, commit:

```
python -m pip install https://github.com/GateNLP/python-gatenlp.git@1.0.7
```

#### Requirements for using the GATE slave:

* Java 8
* py4j
* GATE 8.6.1 or later

#### Requirements for running `gatenlp` in a Jupyter notebook:

* `ipython`
* `jupyter`
* `ipykernel`

To create a kernel for your conda environment run:

```
python -m ipykernel install --user --name gatenlp --display-name "Python gatenlp"
```

The available kernels can be listed with `jupyter kernelspec list`

To run and show a notebook run the following and use "Kernel - Change Kernel" in the notebook to choose the gatenlp environment speicific kernel:

```
jupyter notebook notebookname.ipynb
```

If you prefer Jupyter lab:

```
python -m pip install jupyterlab
```

and then start Jupyter lab with:

```
jupyter lab
```

In Jupyter lab, you can work on Jupyter notebooks but also use an interactive console which is also able to visualize
documents interactively. 
 
#### Requirements for development:

* Java SDK version 8
* Maven version 3.6
