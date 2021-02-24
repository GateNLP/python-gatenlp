# Installation


##  Install Python 

Python version 3.6 or later is required.

There are many different ways of installaing Python, and they should all work, but instructions for how to install, set up environments etc. can be very different depending on the method. 

Therefore, the recommended way is to use Conda by  installing  one of 

* [Anaconda](https://www.anaconda.com/products/individual) or
    * download the installer for your operating system and run it
* [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 
    * download the Python 3.x installer for your operating system and run it

##### On Windows: 

* Install for "Just Me"
* use the default installation location
* register as default python 
* ADD to PATH environment variable: even if not recommended this will simplify using python from GATE and from a Windows command line.
* once installed there will be an "Anaconda" entry in the start menu
* run the powershell prompt or the Anaconda prompt to get a shell for running python, conda etc.

Alternately, 

* [Miniforge](https://github.com/conda-forge/miniforge) may help avoid Windows 10 issues

Alternately,

* Install Python from the Microsoft Store or by downloading the installer from the [Python Download](https://www.python.org/downloads/) page. 
* This will require a different way to create an environment later (use venv!)

##### On linux 

* make the downloaded file executable and run it
* choose installation directory
* allow the installer to activate anaconda (modify .bashrc and put the installed software on the PATH)

## Create Python Environment

Open a terminal/command line. On Windows open an Anaconda Prompt or Powershell. 

If you did install a different Python distribution use `venv` or a similar way to create an environment for gatenlp.

Now create a separate environment for working with gatenlp. This example
creates an environment with the name `gatenlp` and activates it:

```
conda create -n gatenlp python==3.8
conda activate gatenlp
```

The `gatenlp` package has a number of optional dependencies which are only needed if some special features of gatenlp are used.

Install `gatenlp` with all dependencies and support for showing slides: 

```
python -m pip install -U gatenlp[all,dev] 
python -m pip install RISE
```

NOTE: if this fails because of a problem installing torch (this may happen on Windows), 
first install Pytorch separately according to 
the Pytorch installation instructions, see: https://pytorch.org/get-started/locally/
then run the gatenlp installation again. 

Setup a Jupyter kernel for this environment:

```
python -m ipykernel install --user --name gatenlp --display-name "Python-gatenlp"
```

### Windows 10 Kernel Error

There is a bug in Anaconda/Miniconda which may cause an exception when Jupyter tries to initialize the kernel for the notebook. The error will contain the following:

```
import win32api
ImportError: DLL load failed: The specified procedure could not be found.
```

If this happens try to run something like: 
```
python C:\Users\USERNAME\miniconda3\envs\gatenlp\Scripts\pywin32_postinstall.py -install
```

where USERNAME is your user name on Windows.  For an anaconda installation use the corresponding directory instead. 


#### Requirements for using the GATE slave:

* Java 8 or later
* GATE 8.6.1 or later
