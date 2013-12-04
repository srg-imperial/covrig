#!/bin/bash

die () {
    echo >&2 "$@"
    exit 1
}

IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"

INPUT=$1
OUTPUT=$2

egrep -v "$IGNOREREVS" $INPUT |awk 'BEGIN { FS="," } ; { if ($2 > 0) print NR,$4; }' >elocs

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
"$SCRIPT_DIR/internal/lineplot.sh" elocs "$OUTPUT" "Revision" "TLOC" 'set size 0.8,0.8'

rm -f elocs
