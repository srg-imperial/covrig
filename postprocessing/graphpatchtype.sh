#!/bin/bash

die () {
    echo >&2 "$@"
    exit 1
}

IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"

INPUT=$1
OUTPUT=$2

ONLYEXECUTABLE=$(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if (($7 > 0 || $8 > 0) && $26 == 0) print 1 }'|wc -l)
ONLYTEST=$(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($7 == 0 && $8 == 0 && $26 > 0) print 1 }'|wc -l)
TESTANDEXECUTABLE=$(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if (($7 > 0 || $8 > 0) && $26 > 0) print 1 }'|wc -l)
REVISIONS=$(egrep -v "$IGNOREREVS" $1|wc -l)
OTHER=$(($REVISIONS-$ONLYEXECUTABLE-$ONLYTEST-$TESTANDEXECUTABLE))

echo ${OUTPUT:11} $ONLYEXECUTABLE $TESTANDEXECUTABLE $ONLYTEST $OTHER

