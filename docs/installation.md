# Installation

Make sure you have Python 3.5 or later installed.
The recommended way to install conda is to install 
[Anaconda](https://www.anaconda.com/products/individual) or
[Miniconda](https://docs.conda.io/en/latest/miniconda.html).
Then create an environment for working with gatenlp. This example
creates an environment with the name `gatenlp` and activates it:

```
conda create -n gatenlp python==3.8
conda activate gatenlp
```


To install `gatenlp` run:

```
python -m pip install gatenlp 
```

To install the latest `gatenlp` code from GitHub:
* Clone the repository and change into it
* Run `python -m pip -e .`


## Requirements

`gatenlp` components use a wide range of other packages and can interact with
a wide variety of NLP tools. Rather than pulling in all dependencies when
installing, `gatenlp` only requires a few essential packages and leaves it
to the users to install additional packages only if they want to use the
component that needs them. Here is an overview over the basic requirements
and groups of packages needed for specific components:

#### Basic requirements:

* in file `requirements.txt`
* `sortedcontainers>=2.0.0` - gets installed with `gatenlp`
* `requests`

#### Requirements for saving/loading/importing/exporting:

* these are for anything beyond the bdoc-JSON standard format
* `msgpack`
* `pyyaml`
* `bs4`

#### Requirements for using the GATE slave:

* Java 8
* py4j
* GATE 8.6.1 or later

#### Requirements for using the bridges to other NLP tools:

* for StanfordNLP: `stanfordnlp`
* for Stanford Stanza: `stanza`
* for Spacy: `spacy`
* for NLTK: `nltk`

#### Requirements for running `gatenlp` in a Jupyter notebook:

* `ipython`
* `jupyter`
* `ipykernel`

To create a kernel for your conda environment run:

```
python -m ipykernel install --user --name gatenlp --display-name "Python gatenlp"
```

To run and show a notebook run the following and use "Kernel - Change Kernel" in the notebook to choose the gatenlp environment speicific kernel:

```
jupyter notebook notebookname.ipynb
```
 
#### Requirements for development:

* `sphinx`
* Java SDK version 8
* Maven version 3.6
