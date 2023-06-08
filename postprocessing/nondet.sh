#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
INITIAL_DIR="$(pwd)"
IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"
SELECTACTUALCODEORTEST="awk 'BEGIN { FS=\",\" } ; { if (\$7 > 0 || \$8 > 0 || \$26 > 0) print \$1 }'"
MAXNONDET=500
#REVISIONS=250

die () {
    echo >&2 "$@"
    exit 1
}


[ $# -gt 2 ] || die "Usage: $0 [--only-ok] csvfile outputfolder1 outputfolder2 ... outputfoldern"

OK=""
LATEX=0
VARPREFIX="program"
while (( "$#" )); do
  case $1 in
    -o|--only-ok) #only consider revisions where the testsuite terminates with an OK status
      OK=",OK,"
    ;;
    -l|--latex)
      LATEX=1
    ;;
    -p=*|--prefix=*)
      VARPREFIX="${1#*=}"
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

# REVISIONS = the number of lines in REVFILE minus one (since revs in question should already compile etc)
REVISIONS=$(wc -l $REVFILE | awk '{print $1}')
REVISIONS=$((REVISIONS-1))

ACTUALREVS=$($SCRIPT_DIR/internal/goodtobad.sh $REVFILE $REVISIONS)
TOTALALLOK=0
TOTALALLFAILED=0
TOTALCONTRIB=0

for R in $(tail -$ACTUALREVS $REVFILE | egrep -v $IGNOREREVS | eval $SELECTACTUALCODEORTEST); do
  MAXDIFF=-1
  ALLOK=1
  ALLFAILED=1
  for ((i=0; i < $FOLDERCNT-1; i++ ));  do
    if grep $R ${FOLDERS[i]}/*.csv|grep -q ",OK,"; then
      ALLFAILED=0
    else
      ALLOK=0
    fi
    for ((j=i+1; j < $FOLDERCNT; j++ ));  do
      if grep $R ${FOLDERS[i]}/*.csv|grep -q "$OK" && grep $R ${FOLDERS[j]}/*.csv | grep -q "$OK"; then
        if [ -f "${FOLDERS[$i]}/coverage-$R.tar.bz2" ] && [ -f "${FOLDERS[$j]}/coverage-$R.tar.bz2" ]; then
          rm -rf tmp/nondet1 tmp/nondet2
          mkdir -p tmp/nondet1 tmp/nondet2
          tar xjf "${FOLDERS[$i]}/coverage-$R.tar.bz2" -C tmp/nondet1 --wildcards '*total.info'
          tar xjf "${FOLDERS[$j]}/coverage-$R.tar.bz2" -C tmp/nondet2 --wildcards '*total.info'
  
          CDIFF=$($SCRIPT_DIR/internal/nondetone.sh tmp/nondet1/total.info tmp/nondet2/total.info)
          #use a limit that makes sense for the difference in line count. this avoids artefacts created
          #by test suites which kill the programs (lighttpd)
          if [[ "$CDIFF" -gt $MAXDIFF && ( "$CDIFF" -lt $MAXNONDET ) ]]; then
            MAXDIFF=$CDIFF
          fi
          echo $CDIFF >> "tmp/nondet-$i-$j"
        else
          echo "${FOLDERS[$i]}/coverage-$R.tar.bz2" or "${FOLDERS[$j]}/coverage-$R.tar.bz2" not found
        fi
      fi

      if grep $R ${FOLDERS[j]}/*.csv|grep -q ",OK,"; then
        ALLFAILED=0
      else
        ALLOK=0
      fi
    done
  done
  if [[ $MAXDIFF -ge 0 ]]; then
    echo $R $MAXDIFF >> "tmp/nondet-max"
  fi
  if [[ $MAXDIFF -gt 0 ]]; then
    ((TOTALCONTRIB += 1))
  fi
  ((TOTALALLOK += $ALLOK))
  ((TOTALALLFAILED += $ALLFAILED))
done

if [[ $LATEX -eq 1 ]]; then
  N2DIGITS='egrep -o "[0-9]+([.][0-9][0-9]?)?" |head -1'

  echo "\\newcommand{\\${VARPREFIX}RevsAllTestsFailed}[0]{$TOTALALLFAILED\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}RevsAllTestsOK}[0]{$TOTALALLOK\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}RevsTestsMixedResults}[0]{$((REVISIONS-TOTALALLFAILED-TOTALALLOK))\\xspace}"
  # this is also defined by covsummary. we may use different data here, so keep it consistent
  echo "%\\renewcommand{\\${VARPREFIX}TransientTestErrs}[0]{$((REVISIONS-TOTALALLOK))\\xspace}"

  NONDETMAX=$(awk '{print $2}' tmp/nondet-max | $SCRIPT_DIR/statistics.pl|egrep -o "max is [0-9.]+"|eval $N2DIGITS )
  NONDETAVG=$(awk '{print $2}' tmp/nondet-max | $SCRIPT_DIR/statistics.pl|egrep -o "mean is [0-9.]+"|eval $N2DIGITS )
  NONDETMEDIAN=$(awk '{print $2}' tmp/nondet-max | $SCRIPT_DIR/statistics.pl|egrep -o "median is [0-9.]+"|eval $N2DIGITS )
  NONDETMODE=$(awk '{print $2}' tmp/nondet-max | $SCRIPT_DIR/statistics.pl|egrep -o "mode is [0-9.]+"|eval $N2DIGITS )
  NONDETSTDEV=$(awk '{print $2}' tmp/nondet-max | $SCRIPT_DIR/statistics.pl|egrep -o "stdev is [0-9.]+"|eval $N2DIGITS )
  echo "\\newcommand{\\${VARPREFIX}NonDetMax}[0]{$NONDETMAX\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}NonDetAverage}[0]{$NONDETAVG\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}NonDetMedian}[0]{$NONDETMEDIAN\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}NonDetMode}[0]{$NONDETMODE\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}NonDetStdev}[0]{$NONDETSTDEV\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}NonDetCount}[0]{$TOTALCONTRIB\\xspace}"
else
  echo -n "***Overall nondeterminism: "
  awk '{print $2}'  tmp/nondet-max |paste -sd+ |bc

  awk '{print $2}'  tmp/nondet-max | $SCRIPT_DIR/statistics.pl

  echo "Revisions where all the tests failed: $TOTALALLFAILED ; where all tests were OK: $TOTALALLOK"
fi
