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

egrep -v "$IGNOREREVS" $INPUT |awk 'BEGIN { FS="," } ; { if ($2 > 0) { if ($30 > 0) print NR,$3*100/$2,$31*100/$30; else print NR,$3*100/$2,0 } }' >$DATAFILE

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
if [[ $GRAPHTYPE == "standalone" ]]; then
  "$SCRIPT_DIR/internal/lineplot.sh" $DATAFILE "$OUTPUT" "Revision" "Coverage" "set size 0.8,0.8
set title \"${OUTPUT:11}\"
set yrange [ 0 : 100 ]" $GRAPHTYPE
  "$SCRIPT_DIR/internal/pointplot2.sh" $DATAFILE "$OUTPUT-lb" "Revision" "Coverage" "set size 0.8,0.8
set title \"${OUTPUT:11}\"
set yrange [ 0 : 100 ]" $GRAPHTYPE
else
  "$SCRIPT_DIR/internal/lineplot.sh" $DATAFILE "$OUTPUT" "Revision" "Coverage" "set title \"${OUTPUT:11}\" offset 0,-0.6
set yrange [ 0 : 100 ]" $GRAPHTYPE
  "$SCRIPT_DIR/internal/pointplot2.sh" $DATAFILE "$OUTPUT-lb" "Revision" "Coverage" "set title \"${OUTPUT:11}\" offset 0,-0.6
set yrange [ 0 : 100 ]" $GRAPHTYPE-lb
fi
#rm -f $DATAFILE
