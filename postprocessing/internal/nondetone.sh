#!/bin/bash

#assuming lines are listed in the same order in both files
#there should be no reason to have them otherwise

egrep '^DA:' "$1" | sed -e 's/[1-9][0-9]*$/1/g' > "$1.p"
egrep '^DA:' "$2" | sed -e 's/[1-9][0-9]*$/1/g' > "$2.p"

#count the diff lines excluding diff metadata
C=$(diff -U0 --minimal "$1.p" "$2.p" | grep 'DA:' | wc -l)
echo $(($C/2))
