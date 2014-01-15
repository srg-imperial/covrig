#!/bin/bash

die () {
    echo >&2 "$@"
    exit 1
}

IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"

INPUT=$1
OUTPUT=$2
GRAPHMODE=${3:-"standard"}
GRAPHTYPE=${4:-"standalone"}

mkdir -p tmp
#OUTPUT should be graphs/...
DATAFILE="tmp/${OUTPUT:7}"

if [[ "$GRAPHMODE" == "standard" ]]; then
  egrep -v "$IGNOREREVS" $INPUT |awk 'BEGIN { FS="," } ; { if ($2 > 0) print NR,$2,$4 }' >$DATAFILE
else
  egrep -v "$IGNOREREVS" $INPUT |awk 'BEGIN { FS="," ; peloc = 0; ptloc = 0; eloc = 0 ; tloc = 0} ;
                                      { if ($2 > 0) { if ($2 != peloc || $7 > 0 || $8 > 0) eloc++; if ($4 != ptloc || $26 > 0) tloc++; print NR,eloc,tloc ; peloc=$2 ; ptloc = $4 ; } }' >$DATAFILE
fi

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
if [[ $GRAPHTYPE == "standalone" ]]; then
  "$SCRIPT_DIR/internal/lineplot2yaxes.sh" $DATAFILE "$OUTPUT" "" "ELOC" "set size 0.8,0.8
set title \"${OUTPUT:11}\"
set yrange [ 0 : ]
set y2label \"TLOC\"" $GRAPHTYPE
else
  "$SCRIPT_DIR/internal/lineplot2yaxes.sh" $DATAFILE "$OUTPUT" "" "ELOC" "set yrange [ 0 : ]
set title \"${OUTPUT:11}\"
set y2label \"TLOC\"" $GRAPHTYPE
fi
#rm -f $DATAFILE
