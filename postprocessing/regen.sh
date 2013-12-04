#!/usr/bin/env bash


# recreate an analytics csv output containing multiple entries for the same revision
# the last entry will always be used. when a repository is given, the revisions
# will also be order accordingly

die () {
    echo >&2 "$@"
    exit 1
}
[ $# -eq 2 ] || [ $# -eq 1 ] || die "Usage: $0 CSVfile [local repository]"

if [ $# -eq 1 ]; then
  declare -A SHAS
  while read line; do
    SHA=$(echo $line | awk 'BEGIN { FS="," } ; { print $1 }')
    if [ X"$SHA" != "X" ] && [ ${#SHA} -gt 2 ]; then
      if [[ ${SHAS[$SHA]} != "1" ]]; then
        grep "$SHA," $1|tail -1
        SHAS[$SHA]=1
      fi
    fi
  done <"$1"
else
  for SHA in $(cd "$2" && git log --reverse --first-parent --format=%h); do
    grep "$SHA," "$1"|tail -1
  done
fi
