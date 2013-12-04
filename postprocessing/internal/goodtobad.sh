#!/usr/bin/env bash

die () {
    echo >&2 "$@"
    exit 1
}
[ $# -eq 2 ] || die "Usage: $0 [csv file] [good revisions]"

IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"

LINE=0
GOODLINE=0
declare -A MAPPING

function goodline() {
  if echo "$1"|egrep -q -v $IGNOREREVS && echo "$1"|awk 'BEGIN { FS="," } ; { if (! ($7 > 0 || $8 > 0 || $26 > 0)) exit 1 }'; then
    return 0
  else
    return 1
  fi
}

while read line; do
  (( LINE += 1))
  if goodline "$line"; then
    (( GOODLINE += 1))
  fi
  MAPPING[$GOODLINE]=$LINE
done <$1

if [[ $GOODLINE -ge "$2" ]]; then
  D=$(($GOODLINE - $2))
  echo $((LINE - MAPPING[$D]))
else
  echo $LINE
fi
