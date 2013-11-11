#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

echo -n "+++Added/modified ELOC: "
grep -v '#' $1 |awk 'BEGIN { FS="," } ; { print $7+$8 }'|paste -sd+ |bc
grep -v '#' $1 |awk 'BEGIN { FS="," } ; { print $7+$8 }'|sort -n | $SCRIPT_DIR/statistics.pl
echo

echo -n "+++Covered lines: "
grep -v '#' $1 |awk 'BEGIN { FS="," } ; { print $7 }'|paste -sd+ |bc
grep -v '#' $1 |awk 'BEGIN { FS="," } ; { print $7 }'|sort -n | $SCRIPT_DIR/statistics.pl
echo

echo -n "+++Not covered lines: "
grep -v '#' $1|awk 'BEGIN { FS="," } ; { print $8 }'|paste -sd+ |bc
grep -v '#' $1 |awk 'BEGIN { FS="," } ; { print $8 }'|sort -n | $SCRIPT_DIR/statistics.pl
echo

echo -n "+++Affected files: "
grep -v '#' $1|awk 'BEGIN { FS="," } ; { print $24 }'|paste -sd+ |bc
grep -v '#' $1 |awk 'BEGIN { FS="," } ; { print $24 }'|sort -n | $SCRIPT_DIR/statistics.pl
echo

echo -n "+++Revisions affecting only test files: "
grep -v '#' $1|awk 'BEGIN { FS="," } ; { print $24-$26 }'|grep '^0$'|wc -l
echo

echo -n "+++Hunks: "
grep -v '#' $1|awk 'BEGIN { FS="," } ; { print $22 }'|paste -sd+ |bc
grep -v '#' $1 |awk 'BEGIN { FS="," } ; { print $22 }'|sort -n | $SCRIPT_DIR/statistics.pl
echo

echo -n "+++Executable hunks: "
grep -v '#' $1|awk 'BEGIN { FS="," } ; { print $23 }'|paste -sd+ |bc
grep -v '#' $1 |awk 'BEGIN { FS="," } ; { print $23 }'|sort -n | $SCRIPT_DIR/statistics.pl
echo

for (( B=10; B<20; B++ )); do
  echo -n "Covered lines from previous $(($B-9)) patches: "
  grep -v '#' $1|awk "BEGIN { FS=\",\" } ; { print \$$B }"|paste -sd+ |bc
done
