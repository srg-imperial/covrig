#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
die () {
    echo >&2 "$@"
    exit 1
}

LATEX=0
VARPREFIX="program"

while (( "$#" )); do
  case $1 in
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

[ $# -gt 2 ] || die "Usage: $0 <repo> <revfile> <covfolder> [csv] [line|br]"

BR=${5:-line}
N2DIGITS='egrep -o "[0-9]+([.][0-9][0-9]?)?" |head -1'

>tmp/faultcov
>tmp/faultcovstats
OE=0
OT=0
TE=0

for SHA in $(sort -u $2); do
  if [[ "X$BR" == "Xbr" ]]; then
    $SCRIPT_DIR/faultcoverage-br.sh $1 $SHA $3 |tee tmp/faultcovone >> tmp/faultcov
  else
    $SCRIPT_DIR/faultcoverage.sh $1 $SHA $3 |tee tmp/faultcovone >> tmp/faultcov
  fi

  if ! grep -q revfail tmp/faultcovone ; then
    COV=$(grep '1$' tmp/faultcovone | wc -l)
    NOTCOV=$(grep '0$' tmp/faultcovone | wc -l)
    echo $COV $((COV+NOTCOV)) >> tmp/faultcovstats
    if ! grep -q 'noexec 1' tmp/faultcovone; then
      if [[ $COV -eq 0 && $NOTCOV -eq 0 ]]; then
        cat tmp/faultcovone
        echo "WTF"
        exit 1
      fi
    fi
  fi

  if [[ $# -gt 3 ]]; then
    ONLYEXEC=$(grep $SHA $4|awk 'BEGIN { FS="," } ; { if (($7 > 0 || $8 > 0) && $26 == 0) print 1 }'|wc -l)
    ONLYTEST=$(grep $SHA $4|awk 'BEGIN { FS="," } ; { if ($7 == 0 && $8 == 0 && $26 > 0) print 1 }'|wc -l)
    TESTANDEXECUTABLE=$(grep $SHA $4|awk 'BEGIN { FS="," } ; { if (($7 > 0 || $8 > 0) && $26 > 0) print 1 }'|wc -l)
    (( OE += ONLYEXEC ))
    (( OT += ONLYTEST ))
    (( TE += TESTANDEXECUTABLE ))
  fi
done

FIXES=$(sort -u $2 | wc -l)
UNHANDLED=$(grep revfail tmp/faultcov | wc -l)
COV=$(grep '1$' tmp/faultcov | wc -l)
NOTCOV=$(grep '0$' tmp/faultcov | wc -l)
NOEXEC=$(grep 'noexec 1' tmp/faultcov | wc -l)
FULLYCOVERED=$(grep 'fullycovered 1' tmp/faultcov | wc -l)

SIZEAVG=$(awk '{ print $2 }' tmp/faultcovstats|sort -n | $SCRIPT_DIR/statistics.pl|egrep -o "mean is [0-9.]+"|eval $N2DIGITS )
SIZEMEDIAN=$(awk '{ print $2 }' tmp/faultcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "median is [0-9.]+"|eval $N2DIGITS )
SIZESTDEV=$(awk '{ print $2 }' tmp/faultcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "stdev is [0-9.]+"|eval $N2DIGITS )

COVAVG=$(awk '{ if ($2 > 0) print $1*100/$2 }' tmp/faultcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "mean is [0-9.]+"|eval $N2DIGITS )
COVMEDIAN=$(awk '{ if ($2 > 0) print $1*100/$2 }' tmp/faultcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "median is [0-9.]+"|eval $N2DIGITS )
COVSTDEV=$(awk '{ if ($2 > 0) print $1*100/$2 }' tmp/faultcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "stdev is [0-9.]+"|eval $N2DIGITS )


if  [[ $LATEX -eq 1 ]]; then
  if [[ "X$BR" != "Xbr" ]]; then
    TYPREFIX=Line
    echo "\\newcommand{\\${VARPREFIX}Bugs}[0]{$((FIXES-UNHANDLED-NOEXEC))\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}BugsWithoutCode}[0]{$NOEXEC\\xspace}"
    if [[ $# -gt 3 ]]; then
      echo "\\newcommand{\\${VARPREFIX}BugsOnlyTests}[0]{$OT\\xspace}"
      echo "\\newcommand{\\${VARPREFIX}BugsOnlyCode}[0]{$OE\\xspace}"
      echo "\\newcommand{\\${VARPREFIX}BugsTestsAndCode}[0]{$TE\\xspace}"
    fi
  else
    TYPREFIX=Branch
    echo "\\newcommand{\\${VARPREFIX}BugsWithoutBranches}[0]{$NOEXEC\\xspace}"
  fi
  echo "\\newcommand{\\${VARPREFIX}BugsTotal${TYPREFIX}}[0]{$((COV+NOTCOV))\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Bug${TYPREFIX}Coverage}[0]{$(echo "scale=1; $COV*100/($COV+$NOTCOV)"|bc)\\%\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}BugsFully${TYPREFIX}Covered}[0]{$((FULLYCOVERED-NOEXEC))\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}BugsFully${TYPREFIX}CoveredPercent}[0]{$(echo "scale=1 ; ($FULLYCOVERED-$NOEXEC)*100/($FIXES-$UNHANDLED)" |bc)\\%\\xspace}"
  echo
  echo "\\newcommand{\\${VARPREFIX}Bug${TYPREFIX}CoverageAverage}[0]{$COVAVG\\%\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Bug${TYPREFIX}CoverageMedian}[0]{$COVMEDIAN\\%\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Bug${TYPREFIX}CoverageStdev}[0]{${COVSTDEV}pp\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Bug${TYPREFIX}SizeAverage}[0]{$SIZEAVG\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Bug${TYPREFIX}SizeMedian}[0]{$SIZEMEDIAN\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Bug${TYPREFIX}SizeStdev}[0]{$SIZESTDEV\\xspace}"
  echo
else
  echo "Looked at $FIXES faults ($UNHANDLED unhandled): $COV lines covered, $NOTCOV lines not covered"
  echo "$NOEXEC faults did not change/remove code, $FULLYCOVERED bugs were fully covered"
  if [[ $# -gt 3 ]]; then
    echo "only tests/only code/tests and code $OT/$OE/$TE"
  fi
fi
