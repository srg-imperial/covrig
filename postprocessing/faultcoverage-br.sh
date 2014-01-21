#!/bin/bash

# script to determine wether bugs are in covered or uncovered code
# first argument is the target git repository
# second argument is a revision (sha of a revision which introduced a bug)
# third argument is a folder which contains the coverage information for the revision
# in the format coverage-<sha>.tar.bz2

die () {
    echo >&2 "$@"
    exit 1
}
[ $# -eq 3 ] || die "Usage: $0 <git repo> <bug introducing rev> <cov info folder>"

REPO=$1
SHA=$2
COV=$3
SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

. $SCRIPT_DIR/internal/covstatus.sh

declare -r git_new_file_regex="\+\+\+ b/(.*)"
declare -r new_hunk_regex="@@.*\+([0-9]+),([0-9]+) @@"
declare -r new_hunk_def_regex="@@.*\+([0-9]+) @@"

PREVSHA=$( cd $REPO && git rev-parse $SHA~1 )
TOTAL_NEW=0
TOTAL_NEW_UNCOVERED=0
CFILE=
COVSTATUS=(0 0 0)
FULLYCOVERED=1
NOEXEC=1

rm -rf faultcov-tmp
mkdir -p tmp
(cd $REPO && git diff -b -U0 $SHA $SHA~1) > tmp/diff

while read line; do
  SLINE=0
  if [[ $line =~ $git_new_file_regex ]]; then
    F=${BASH_REMATCH[1]}
    CFILE=`echo -e $F`
    #echo "captured file" $CFILE
  fi
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
      if [[ ${COVSTATUS[0]} -lt 3 ]]; then
        COVSTATUS=($( is_br_covered "$CFILE" $i $COV $PREVSHA))
        
        if [[ ${COVSTATUS[0]} -ge 3 ]]; then
          echo "$SHA revfail -"
        fi
      fi
      if [[ ${COVSTATUS[0]} -eq 0 ]]; then
        NOEXEC=0
        for ((j=0; j<${COVSTATUS[1]} ; j++)); do
          echo $i 1
        done
        for ((j=0; j<${COVSTATUS[2]} ; j++)); do
          FULLYCOVERED=0
          echo $i 0
        done
      fi
      let i++
    done
  fi
done < tmp/diff

if [[ ${COVSTATUS[0]} -lt 3 ]]; then
  echo "$SHA fullycovered $FULLYCOVERED -"
  echo "$SHA noexec $NOEXEC -"
fi
