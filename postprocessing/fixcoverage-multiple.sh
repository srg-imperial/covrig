#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

>tmpfixcov
OE=0
OT=0
TE=0

for SHA in $(sort -u $2); do
  $SCRIPT_DIR/fixcoverage.sh $1 $SHA $3 >> tmpfixcov
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

echo "Looked at $FIXES fixes ($UNHANDLED unhandled): $COV lines covered, $NOTCOV lines not covered"
echo "$NOEXEC fixes did not change/add code, $FULLYCOVERED fixes were fully covered"
if [[ $# -gt 3 ]]; then
  echo "only tests/only code/tests and code $OT/$OE/$TE"
fi