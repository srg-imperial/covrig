#!/usr/bin/env bash

INPUTS=(data/Redis/Redis.csv data/Zeromq/Zeromq.csv data/Lighttpd/Lighttpd.csv data/Memcached/Memcached.csv data/Binutils/Binutils.csv)
OUTPUTS=(red zmq lgh mem bin)

mkdir -p graphs

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
for ((i=0;i<${#INPUTS[@]};++i)); do
  if [ -f ${INPUTS[$i]} ]; then
    $SCRIPT_DIR/latentcoveragegraph.sh ${INPUTS[$i]} graphs/${OUTPUTS[$i]}
    $SCRIPT_DIR/latentcoveragegraph.sh -r ${INPUTS[$i]} graphs/r${OUTPUTS[$i]}
    $SCRIPT_DIR/patchcoverage.sh ${INPUTS[$i]} graphs/pcov${OUTPUTS[$i]}
    $SCRIPT_DIR/grapheloc.sh ${INPUTS[$i]} graphs/eloc${OUTPUTS[$i]}
    $SCRIPT_DIR/graphtloc.sh ${INPUTS[$i]} graphs/tloc${OUTPUTS[$i]}
  fi
done
