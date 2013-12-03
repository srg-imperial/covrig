#!/bin/bash
#output all the lines modified or added in $2 compared to $1

declare -r git_new_file_regex="\+\+\+ b/(.*)"
declare -r new_hunk_regex="@@.*\+([0-9]+),([0-9]+) @@"
declare -r new_hunk_def_regex="@@.*\+([0-9]+) @@"

die () {
    echo >&2 "$@"
    exit 1
}

[ "$#" -eq 3 ] || die "Usage $0 <rev1> <rev2> <file>"

#if [ ! -f rdiff.tmp ]; then
  git diff -b -U0 $1 $2 > rdiff.tmp
#fi

TOTAL_NEW=0
TOTAL_NEW_UNCOVERED=0
FFOUND=0

while read line; do
  SLINE=0
  if [[ $line =~ $git_new_file_regex ]]; then
    F=${BASH_REMATCH[1]}
    F=`echo -e $F`
    if [[ $F = $3 ]]; then
      FFOUND=1
    else
      FFOUND=0
    fi
    #echo "captured file" $F
  fi
  if [[ $FFOUND -eq 1 ]]; then
    if [[ $line =~ $new_hunk_regex ]]; then
      SLINE=${BASH_REMATCH[1]}
      CLINE=${BASH_REMATCH[2]}
      #echo "found new hunk " $SLINE $CLINE
    elif [[ $line =~ $new_hunk_def_regex ]]; then
      SLINE=${BASH_REMATCH[1]}
      CLINE=1
      #echo "found new dhunk " $SLINE $CLINE
    fi
    if [[ $SLINE -ne 0 ]]; then
      i=$SLINE
      let "LLINE = SLINE + CLINE"
      while [[ $i -lt $LLINE ]]; do
        echo $i
        let i++
      done
    fi
  fi
done < rdiff.tmp

