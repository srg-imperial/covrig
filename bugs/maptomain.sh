#!/usr/bin/env bash

die () {
    echo >&2 "$@"
    exit 1
}

[ $# -eq 3 ] || die "Usage: $0 revfile csv repo"

grep -v '#' $2 | awk 'BEGIN { FS="," } ; { print $1 }' > tmprev
rev0=$(head -1 tmprev)

for c in $(awk '{ print $1 }' $1); do
  if grep -q $c tmprev; then
    echo $c
  else
    if (cd $3 && git rev-list $rev0~1 | egrep -q "^$c"); then
      #this was merged before we started the analysis. ignore
      continue
    fi
    for mc in $(<tmprev); do
      if (cd $3 && git rev-list $mc | egrep -q "^$c"); then
        echo "$mc (for $c)"
        break
      fi
    done
  fi
done
