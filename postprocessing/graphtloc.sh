#!/bin/bash

die () {
    echo >&2 "$@"
    exit 1
}

IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"

INPUT=$1
OUTPUT=$2
GRAPHTYPE=${3:-"standalone"}

mkdir -p tmp
#OUTPUT should be graphs/...
DATAFILE="tmp/${OUTPUT:7}"

egrep -v "$IGNOREREVS" $INPUT |awk 'BEGIN { FS="," } ; { if ($2 > 0) print NR,$4; }' >$DATAFILE

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
if [[ $GRAPHTYPE == "standalone" ]]; then
  "$SCRIPT_DIR/internal/lineplot.sh" $DATAFILE "$OUTPUT" "" "TLOC" "set size 0.8,0.8
set title \"${OUTPUT:11}\"
set style line 1 lc rgb '#CB2027' lt 1 lw 1 pt 1 ps 0.6" $GRAPHTYPE
else
  "$SCRIPT_DIR/internal/lineplot.sh" $DATAFILE "$OUTPUT" "" "TLOC" "set title \"${OUTPUT:11}\" offset 0,-0.6
set style line 1 lc rgb '#CB2027' lt 1 lw 1 pt 1 ps 0.6" $GRAPHTYPE
fi

#rm -f $DATAFILE
