# Various Notes about Development




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
* upload to pypi
* created annotated tag v9.9
* increase the gatenlp version

## Run pytest

For a test with some keyword and set logging level:

`pytest -k test_call3 -s --log-cli-level=DEBUG`
