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

#egrep -v "$IGNOREREVS" $INPUT |awk 'BEGIN { FS=","; peloc=0; } ; { if (($7 > 0 || $8 > 0) && peloc > 0) print NR,2*($7+$8)-($2-peloc); peloc=$2; }'|sort -n -k 2 >$DATAFILE
#egrep -v "$IGNOREREVS" $INPUT |awk 'BEGIN { FS=","; peloc=0; } ; { if (($7 > 0 || $8 > 0) && peloc > 0) print NR,2*($7+$8)-($2-peloc); peloc=$2; }'|sort -n -k 2 >$DATAFILE
egrep -v "$IGNOREREVS" $INPUT |awk 'BEGIN { FS=","; peloc=0; } ; { if (($7 > 0 || $8 > 0)) print NR,$25; }'|sort -n -k 2 >$DATAFILE

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
if [[ $GRAPHTYPE == "standalone" ]]; then
  "$SCRIPT_DIR/internal/lineplot.sh" $DATAFILE "$OUTPUT" "Revision" "Lines" "set size 0.8,0.8
set title \"${OUTPUT:11}\"
set yrange [ 0 : 600 ]" $GRAPHTYPE
else
  "$SCRIPT_DIR/internal/lineplot.sh" $DATAFILE "$OUTPUT" "Revision" "Lines" "set yrange [ 0 : 600 ]
set title \"${OUTPUT:11}\"" $GRAPHTYPE
fi
#rm -f $DATAFILE
