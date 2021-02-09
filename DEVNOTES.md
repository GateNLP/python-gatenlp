# Various Notes about Development

## Use a prepared environment in a Jupyter notebook

* `pip install ipykernel`
* within the env: `python -m ipykernel install --user --name envname --display-name "Python (envname)`
* To list which are already there: `jupyter kernelspec list`


## Prepare a release

For now rather simple:

* make sure everything is pulled and we are on branch master
* make sure it works: run tests
* !! make sure the latest version of the htmlviewer javascript is released
  and the correct version number is used in the serializer and 
  * `python make-viewer.py` has been run to copy to the package directory
* !! make sure the version has been updated to what we want to release!
* run ./gendoc-pdoc3.sh
* add anything that needs to get added

* !! SYNC WITH UPCOMING PYTHON PLUGIN RELEASE:
* Edit: `java/src/main/java/gate/tools/gatenlpslave/GatenlpWorker.java`
  and change the version of python plugin to the upcoming one which will contain the new GateNLP release
* run `python make-java.py` 
* re-install current directory locally using `pip install -e .[all,dev]`
* double check that gateworker tries to load the new (not-yet existing) release
* commit and push
* create release branch and push 
* commit and push, we have now pushed exactly what will be the gatenlp release

* In plugin Python:
  * pull, make sure ready for release
  * `git submodue update --remote` 
  * commit/push/check it compiles
  * this is now the version we can release, which contains the submodule commit of what will be the gatenlp release
  * Actually create the Python plugin release the normal way
  * wait until available on Maven Central
  
* upload to pypi
* create annotated tag v9.9
* !! GateNLP is now released!
* checkout master
* increase the gatenlp version
* edit `java/src/main/java/gate/tools/gatenlpslave/GatenlpWorker.java` and change version
  to next Python plugin snapshot
* create next Python plugin snapshot

## Run pytest

For a test with some keyword and set logging level:

`pytest -k test_call3 -s --log-cli-level=DEBUG`
