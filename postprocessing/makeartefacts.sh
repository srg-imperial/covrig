#!/usr/bin/env bash

INPUTS=(data/Redis/Redis.csv data/Zeromq/Zeromq.csv data/Lighttpd/Lighttpd.csv data/Memcached/Memcached.csv data/Binutils/Binutils.csv)
OUTPUTS=(redis zeromq lighttpd memcached binutils)

REVISIONS=250

mkdir -p graphs latex

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
for ((i=0;i<${#INPUTS[@]};++i)); do
  if [ -f ${INPUTS[$i]} ]; then
    ACTUALREVS=$($SCRIPT_DIR/internal/goodtobad.sh ${INPUTS[$i]} $REVISIONS)
    tail -$ACTUALREVS ${INPUTS[$i]} > outptmp

    $SCRIPT_DIR/latentcoveragegraph.sh outptmp graphs/${OUTPUTS[$i]}
    $SCRIPT_DIR/latentcoveragegraph.sh -r outptmp graphs/r${OUTPUTS[$i]}
    $SCRIPT_DIR/patchcoverage.sh outptmp graphs/pcov${OUTPUTS[$i]}
    $SCRIPT_DIR/grapheloc.sh outptmp graphs/eloc${OUTPUTS[$i]}
    $SCRIPT_DIR/graphtloc.sh outptmp graphs/tloc${OUTPUTS[$i]}

    $SCRIPT_DIR/covsummary.sh --latex --prefix=${OUTPUTS[$i]} outptmp > latex/${OUTPUTS[$i]}.tex
  fi
done

rm -f outptmp
