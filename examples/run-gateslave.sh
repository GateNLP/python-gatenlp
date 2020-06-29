#!/bin/bash

# NOTE: run this script from the root of the repo!

if [ "x${GATE_HOME}" == "x" ]
then
  echo Environment variable GATE_HOME not set
  exit 1
fi

if [[ -f "${GATE_HOME}/gate.classpath" ]]
then
  gatecp=`cat "${GATE_HOME}/gate.classpath"`
else
  if [[ -d "${GATE_HOME}/lib" ]]
  then
    gatecp="${GATE_HOME}/lib/"'*'
  else
    echo Could not find $GATE_HOME/gate.classpath nor $GATE_HOME/lib
    exit 1
  fi
fi

java -classpath "$gatecp:${GATE_HOME}/bin:java/target/gatetools-gatenlpslave-1.0.jar" gate.tools.gatenlpslave.GatenlpSlave "$@"

