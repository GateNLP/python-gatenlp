# Various Notes about Development

## Use a prepared environment in a Jupyter notebook

* `pip install ipykernel`
* within the env: `python -m ipykernel install --user --name envname --display-name "Python (envname)`
* To list which are already there: `jupyter kernelspec list`


## Prepare a release

For now rather simple:

* make sure it works
* make sure the latest version of the htmlviewer javascript is released
  and the correct version is used in the serializer
* run ./gendoc-pdoc3.sh
* commit/push
* Do: `touch java/src/main/java/gate/tools/gatenlpslave/GatenlpSlave.java`
* run ./make.sh test
* make sure the maven build worked!
* !!! Now create a new plugin Python release with this versions and wait until available on Central
* Once available update the GatenlpSlave.java file to load the new Plugin version!
* run python make-java.py
* re-install gatenlp locally and make sure the gatenlp-gate-slave loads the correct Python plugin
* commit and push
* create and checkout a version n.n branch (no "v" in front), push the branch
* upload to pypi
* create annotated tag v9.9
* checkout master
* increase the gatenlp version

## Run pytest

For a test with some keyword and set logging level:

`pytest -k test_call3 -s --log-cli-level=DEBUG`
