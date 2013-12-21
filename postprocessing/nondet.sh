#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
INITIAL_DIR="$(pwd)"
IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"
SELECTACTUALCODEORTEST="awk 'BEGIN { FS=\",\" } ; { if (\$7 > 0 || \$8 > 0 || \$26 > 0) print \$1 }'"
MAXNONDET=100
REVISIONS=250

die () {
    echo >&2 "$@"
    exit 1
}


[ $# -gt 2 ] || die "Usage: $0 [--only-ok] csvfile outputfolder1 outputfolder2 ... outputfoldern"

OK=""
while (( "$#" )); do
  case $1 in
    -o|--only-ok) #only consider revisions where the testsuite terminates with an OK status
      OK=",OK,"
    ;;
    *)
      break;
    ;;
  esac
  shift
done

[ -f "$1" ] || die "File does not exist: $1"

REVFILE="$1"
shift
FOLDERCNT=$#

declare -a FOLDERS
for F in "$@"; do
  [ -d "$F" ] || die "Folder does not exist: $F"
  FOLDERS+=("$F")
done

rm -f tmp/nondet-*

ACTUALREVS=$($SCRIPT_DIR/internal/goodtobad.sh $REVFILE $REVISIONS)

for R in $(tail -$ACTUALREVS $REVFILE | egrep -v $IGNOREREVS | eval $SELECTACTUALCODEORTEST); do
  MAXDIFF=-1
  for ((i=0; i < $FOLDERCNT-1; i++ ));  do
    for ((j=i+1; j < $FOLDERCNT; j++ ));  do
      if grep $R ${FOLDERS[i]}/*.csv|grep -q "$OK" && grep $R ${FOLDERS[j]}/*.csv | grep -q "$OK"; then
        if [ -f "${FOLDERS[$i]}/coverage-$R.tar.bz2" ] && [ -f "${FOLDERS[$j]}/coverage-$R.tar.bz2" ]; then
          rm -rf tmp/nondet1 tmp/nondet2
          mkdir -p tmp/nondet1 tmp/nondet2
          tar xjf "${FOLDERS[$i]}/coverage-$R.tar.bz2" -C tmp/nondet1 --wildcards '*total.info'
          tar xjf "${FOLDERS[$j]}/coverage-$R.tar.bz2" -C tmp/nondet2 --wildcards '*total.info'
  
          CDIFF=$($SCRIPT_DIR/internal/nondetone.sh tmp/nondet1/total.info tmp/nondet2/total.info)
          if [[ "$CDIFF" -gt $MAXDIFF && "$CDIFF" -lt $MAXNONDET ]]; then
            MAXDIFF=$CDIFF
          fi
          echo $CDIFF >> "tmp/nondet-$i-$j"
        else
          echo "${FOLDERS[$i]}/coverage-$R.tar.bz2" or "${FOLDERS[$j]}/coverage-$R.tar.bz2" not found
        fi
      fi
    done
  done
  if [[ $MAXDIFF -ge 0 ]]; then
    echo $R $MAXDIFF >> "tmp/nondet-max"
  fi
done

echo -n "***Overall nondeterminism: "
awk '{print $2}'  tmp/nondet-max |paste -sd+ |bc

awk '{print $2}'  tmp/nondet-max | $SCRIPT_DIR/statistics.pl

