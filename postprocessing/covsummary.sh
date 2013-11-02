#!/bin/bash


echo -n "Covered lines: "
cat $1 |awk 'BEGIN { FS="," } ; { print $7 }'|grep -v '#'|paste -sd+ |bc
echo -n "Not covered lines: "
cat $1 |awk 'BEGIN { FS="," } ; { print $8 }'|grep -v '#'|paste -sd+ |bc

for (( B=10; B<20; B++ )); do
  echo -n "Covered lines from previous $(($B-9)) patches: "
  grep -v '#' $1|awk "BEGIN { FS=\",\" } ; { print \$$B }"|paste -sd+ |bc
done
