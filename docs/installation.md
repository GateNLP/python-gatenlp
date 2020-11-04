# Installation

Make sure you have Python 3.6 or later installed. Python version 3.7 or later is highly recommended!

The recommended way to install Python is to use Conda by installing  one of 

* [Anaconda](https://www.anaconda.com/products/individual) or
* [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

Then create an environment for working with gatenlp. This example
creates an environment with the name `gatenlp` and activates it:

```
conda create -n gatenlp python==3.8
conda activate gatenlp
```

The gatenlp has a number of optional dependencies which are only needed if
some special features of gatenlp are used.

To install `gatenlp` with the minimal set of dependencies run:

```
python -m pip install gatenlp 
```

To install `gatenlp` with all dependencies run:

```
python -m pip install gatenlp[all]
```

NOTE: if this fails because of a problem installing torch (this may happen on Windows), 
first install Pytorch separately according to 
the Pytorch installation instructions, see: https://pytorch.org/get-started/locally/
then run the gatenlp installation again. 

The following specific dependencies can be chosen:
* `formats`: to support the various serialization formats
* `java`: to support the Gate slave 
* `stanza`: to support the Stanza bridge
* `spacy`: to support the Spacy bridge
* `standfordnlp`: to support the StanfordNLP bridge (may get removed in a later version)
* `nltk`: to support the nltk tokenizer and nltk bridge
* `gazetteers`: to support gazetteers
* `dev`: dependencies needed for developing gatenlp 

To install gatenlp with support for stanza and spacy and serialization:

```
python -m pip install gatenlp[stanza,spacy,formats]
```



To install the latest `gatenlp` code from GitHub with all dependencies:
* Clone the repository and change into it
* Run `python -m pip -e .[all]`


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
