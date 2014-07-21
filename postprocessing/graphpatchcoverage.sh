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
>$DATAFILE

  #number of revisions which introduce executable code
  TOTALREVS=$(egrep -v "$IGNOREREVS" $1 | awk 'BEGIN { FS="," } ; { if ($7+$8 > 0) print 1}'|wc -l)

  declare -a BUCKETS
  BUCKETS[0]=-1
  BUCKETS[1]=0
  BUCKETS[2]=0.25
  BUCKETS[3]=0.5
  BUCKETS[4]=0.75
  BUCKETS[5]=1

  #LaTeX doesn't allow digits in command names
  echo -n "${OUTPUT:11} "

  declare -a BUCKETNAMES
  BUCKETNAMES[0]="Zero"
  BUCKETNAMES[1]="Q"
  BUCKETNAMES[2]="H"
  BUCKETNAMES[3]="3Q"
  BUCKETNAMES[4]="N/A"
  for BUCKETIDX in 0 1 2 3 4; do
     AWKSCRIPT="BEGIN { FS=\",\" } ; {
     if (\$7+\$8 > 0 && \$7/(\$7+\$8) > ${BUCKETS[$BUCKETIDX]} &&
       \$7/(\$7+\$8) <= ${BUCKETS[$((BUCKETIDX+1))]}) {
                    print \$7/(\$7+\$8)
                  }
                }"
    #this is the number of patches which get coverage in the current range
    BUCKETENTRIES=$(egrep -v "$IGNOREREVS" $1 |awk "$AWKSCRIPT" | wc -l);
    BUCKETENTRIESPERCENT=$(echo "scale=2 ; $BUCKETENTRIES*100/$TOTALREVS" |bc)
    echo -n "$BUCKETENTRIESPERCENT "
    #echo "${BUCKETS[$BUCKETIDX]}-${BUCKETS[$((BUCKETIDX+1))]} " $BUCKETENTRIES >>$DATAFILE
  done
  echo
#SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
#if [[ $GRAPHTYPE == "standalone" ]]; then
#  "$SCRIPT_DIR/internal/histogram.sh" $DATAFILE "$OUTPUT" "Coverage" "" "set size 0.8,0.8
#set title \"${OUTPUT:11}\"" $GRAPHTYPE
#else
#  "$SCRIPT_DIR/internal/histogram.sh" $DATAFILE "$OUTPUT" "Coverage" "" "set title \"${OUTPUT:11}\" offset 0,-0.6" $GRAPHTYPE
#fi
#rm -f $DATAFILE
