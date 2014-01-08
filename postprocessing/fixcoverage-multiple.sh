#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

>tmpfixcov
for SHA in $(sort -u $2); do
  $SCRIPT_DIR/fixcoverage.sh $1 $SHA $3 >> tmpfixcov
done

FIXES=$(sort -u $2 | wc -l)
UNHANDLED=$(grep revfail tmpfixcov | wc -l)
COV=$(grep '1$' tmpfixcov | wc -l)
NOTCOV=$(grep '0$' tmpfixcov | wc -l)
NOEXEC=$(grep 'noexec 1' tmpfixcov | wc -l)
FULLYCOVERED=$(grep 'fullycovered 1' tmpfixcov | wc -l)

echo "Looked at $FIXES fixes ($UNHANDLED unhandled): $COV lines covered, $NOTCOV lines not covered"
echo "$NOEXEC fixes did not change/add code, $FULLYCOVERED fixes were fully covered"
