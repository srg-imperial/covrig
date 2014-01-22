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

>tmpfixcov
OE=0
OT=0
TE=0

for SHA in $(sort -u $2); do
  if [[ "X$BR" == "Xbr" ]]; then
    $SCRIPT_DIR/fixcoverage-br.sh $1 $SHA $3 >> tmpfixcov
  else
    $SCRIPT_DIR/fixcoverage.sh $1 $SHA $3 >> tmpfixcov
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
UNHANDLED=$(grep revfail tmpfixcov | wc -l)
COV=$(grep '1$' tmpfixcov | wc -l)
NOTCOV=$(grep '0$' tmpfixcov | wc -l)
NOEXEC=$(grep 'noexec 1' tmpfixcov | wc -l)
FULLYCOVERED=$(grep 'fullycovered 1' tmpfixcov | wc -l)

if  [[ $LATEX -eq 1 ]]; then
  if [[ "X$BR" != "Xbr" ]]; then
    TYPREFIX=Line
    #this is the same for line/branch. output it once
    echo "\\newcommand{\\${VARPREFIX}Bugs}[0]{$((FIXES-UNHANDLED))\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}FixesWithoutCode}[0]{$NOEXEC\\xspace}"
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
  echo "\\newcommand{\\${VARPREFIX}Fix${TYPREFIX}Coverage}[0]{$(echo "scale=1; $COV*100/($COV+$NOTCOV)"|bc)\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}FixesFully${TYPREFIX}Covered}[0]{$((FULLYCOVERED-NOEXEC))\\xspace}"
else
  echo "Looked at $FIXES fixes ($UNHANDLED unhandled): $COV lines covered, $NOTCOV lines not covered"
  echo "$NOEXEC fixes did not change/add code, $FULLYCOVERED fixes were fully covered"
  if [[ $# -gt 3 ]]; then
    echo "only tests/only code/tests and code $OT/$OE/$TE"
  fi
fi
