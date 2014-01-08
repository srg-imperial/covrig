#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

>tmpfaultcov
for SHA in $(sort -u $2); do
  $SCRIPT_DIR/faultcoverage.sh $1 $SHA $3 >> tmpfaultcov
done

FIXES=$(sort -u $2 | wc -l)
UNHANDLED=$(grep revfail tmpfaultcov | wc -l)
COV=$(grep '1$' tmpfaultcov | wc -l)
NOTCOV=$(grep '0$' tmpfaultcov | wc -l)
NOEXEC=$(grep 'noexec 1' tmpfaultcov | wc -l)
FULLYCOVERED=$(grep 'fullycovered 1' tmpfaultcov | wc -l)

echo "Looked at $FIXES faults ($UNHANDLED unhandled): $COV lines covered, $NOTCOV lines not covered"
echo "$NOEXEC faults did not change/remove code, $FULLYCOVERED bugs were fully covered"
