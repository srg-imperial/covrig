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
IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"

#XXX: patches with more than 127 ELOC are not supported
latent_coverage () {
  local REV=$1
  local CSVFILE=$2
  local cov=0
  if grep -A 1 $REV $CSVFILE | tail -1| egrep -q -v $IGNOREREVS; then
    cov=$(grep -A 1 $REV $CSVFILE | tail -1 |awk 'BEGIN { FS="," } ; { print $10}')
  fi
  for (( i=1 ; i<10; i++ )); do
    if grep -A $((i+1)) $REV $CSVFILE | tail -1| egrep -q -v $IGNOREREVS; then
      LATENT=$(grep -A $((i+1)) $REV $CSVFILE | tail -1 |awk 'BEGIN { FS="," } ; { print $'$((i+10))'-$'$((i+9))'}')
      if [[ $LATENT -lt 0 ]]; then exit; fi
      ((cov += LATENT))
    fi
  done

  return $cov
}

mkdir -p tmp
>tmp/fixcov
>tmp/fixcovstats
OE=0
OT=0
TE=0
LATENTCOV=0

for SHA in $(sort -u $2); do
  if [[ "X$BR" == "Xbr" ]]; then
    $SCRIPT_DIR/fixcoverage-br.sh $1 $SHA $3 | tee tmp/fixcovone >> tmp/fixcov
  else
    $SCRIPT_DIR/fixcoverage.sh $1 $SHA $3 | tee tmp/fixcovone >> tmp/fixcov
  fi
  
  if ! grep -q revfail tmp/fixcovone ; then
    COV=$(grep '1$' tmp/fixcovone | wc -l)
    NOTCOV=$(grep '0$' tmp/fixcovone | wc -l)
    echo $COV $((COV+NOTCOV)) >> tmp/fixcovstats
    latent_coverage $SHA "$4"
    ((LATENTCOV += $?))
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
UNHANDLED=$(grep revfail tmp/fixcov | wc -l)
COV=$(grep '1$' tmp/fixcov | wc -l)
NOTCOV=$(grep '0$' tmp/fixcov | wc -l)
NOEXEC=$(grep 'noexec 1' tmp/fixcov | wc -l)
FULLYCOVERED=$(grep 'fullycovered 1' tmp/fixcov | wc -l)

SIZEAVG=$(awk '{ print $2 }' tmp/fixcovstats|sort -n | $SCRIPT_DIR/statistics.pl|egrep -o "mean is [0-9.]+"|eval $N2DIGITS )
SIZEMEDIAN=$(awk '{ print $2 }' tmp/fixcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "median is [0-9.]+"|eval $N2DIGITS )
SIZESTDEV=$(awk '{ print $2 }' tmp/fixcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "stdev is [0-9.]+"|eval $N2DIGITS )

COVAVG=$(awk '{ if ($2 > 0) print $1*100/$2 }' tmp/fixcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "mean is [0-9.]+"|eval $N2DIGITS )
COVMEDIAN=$(awk '{ if ($2 > 0) print $1*100/$2 }' tmp/fixcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "median is [0-9.]+"|eval $N2DIGITS )
COVSTDEV=$(awk '{ if ($2 > 0) print $1*100/$2 }' tmp/fixcovstats |sort -n| $SCRIPT_DIR/statistics.pl|egrep -o "stdev is [0-9.]+"|eval $N2DIGITS )

if  [[ $LATEX -eq 1 ]]; then
  if [[ "X$BR" != "Xbr" ]]; then
    TYPREFIX=Line
    #this is the same for line/branch. output it once
    echo "\\newcommand{\\${VARPREFIX}Fixes}[0]{$((FIXES-UNHANDLED-NOEXEC))\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}FixesWithoutCode}[0]{$NOEXEC\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}FixesLatentLineCoverage}[0]{$LATENTCOV\\xspace}"
    if [[ $# -gt 3 ]]; then
      echo "\\newcommand{\\${VARPREFIX}FixesOnlyTests}[0]{$OT\\xspace}"
      echo "\\newcommand{\\${VARPREFIX}FixesOnlyCode}[0]{$OE\\xspace}"
      echo "\\newcommand{\\${VARPREFIX}FixesTestsAndCode}[0]{$TE\\xspace}"
    fi
  else
    TYPREFIX=Branch
    echo "\\newcommand{\\${VARPREFIX}FixesWithoutBranches}[0]{$NOEXEC\\xspace}"
  fi
  echo "\\newcommand{\\${VARPREFIX}FixesTotal${TYPREFIX}}[0]{$((COV+NOTCOV))\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Fix${TYPREFIX}Coverage}[0]{$(echo "scale=1; $COV*100/($COV+$NOTCOV)"|bc)\\%\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}FixesFully${TYPREFIX}Covered}[0]{$((FULLYCOVERED-NOEXEC))\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}FixesFully${TYPREFIX}CoveredPercent}[0]{$(echo "scale=1 ; ($FULLYCOVERED-$NOEXEC)*100/($FIXES-$UNHANDLED-$NOEXEC)" |bc)\\%\\xspace}"
  echo
  echo "\\newcommand{\\${VARPREFIX}Fix${TYPREFIX}CoverageAverage}[0]{$COVAVG\\%\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Fix${TYPREFIX}CoverageMedian}[0]{$COVMEDIAN\\%\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Fix${TYPREFIX}CoverageStdev}[0]{${COVSTDEV}pp\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Fix${TYPREFIX}SizeAverage}[0]{$SIZEAVG\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Fix${TYPREFIX}SizeMedian}[0]{$SIZEMEDIAN\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}Fix${TYPREFIX}SizeStdev}[0]{$SIZESTDEV\\xspace}"
  echo
else
  echo "Looked at $FIXES fixes ($UNHANDLED unhandled): $COV lines covered, $NOTCOV lines not covered"
  echo "$NOEXEC fixes did not change/add code, $FULLYCOVERED fixes were fully covered"
  if [[ $# -gt 3 ]]; then
    echo "only tests/only code/tests and code $OT/$OE/$TE"
  fi
fi
