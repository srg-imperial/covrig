#!/bin/bash

# script to determine wether bugs are in covered or uncovered code
# first argument is the target git repository
# second argument is a revision (sha of a revisions which have been determined to be a fix)
# third argument is a folder which contains the coverage information for the revision
# in the format coverage-<sha>.tar.bz2

#NB: we can also use the data in the csv output for fixes (but not for bugs)
#so the same approch (getting the coverage from the lcov info) was used for consistency

die () {
    echo >&2 "$@"
    exit 1
}
[ $# -eq 3 ] || die "Usage: $0 <git repo> <bug fixes rev> <cov info folder>"

declare -r git_new_file_regex="\+\+\+ b/(.*)"
declare -r new_hunk_regex="@@.*\+([0-9]+),([0-9]+) @@"
declare -r new_hunk_def_regex="@@.*\+([0-9]+) @@"

REPO=$1
SHA=$2
COV=$3
SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

. $SCRIPT_DIR/internal/covstatus.sh

TOTAL_NEW=0
TOTAL_NEW_UNCOVERED=0
CFILE=
COVSTATUS=0
FULLYCOVERED=1
NOEXEC=1

rm -rf faultcov-tmp
mkdir -p tmp
(cd $REPO && git diff -b -U0 $SHA~1 $SHA) > tmp/diff

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
      if [[ $COVSTATUS -lt 3 ]]; then
        is_covered "$CFILE" $i $COV $SHA
        COVSTATUS=$?
        if [[ $COVSTATUS -ge 3 ]]; then
          echo "$SHA revfail -"
        fi
      fi
      if [[ $COVSTATUS -lt 2 ]]; then
        NOEXEC=0
      fi
      if [[ $COVSTATUS -eq 0 ]]; then
        FULLYCOVERED=0
      fi
      echo $i $COVSTATUS
      let i++
    done
  fi
done < tmp/diff

if [[ $COVSTATUS -lt 3 ]]; then
  echo "$SHA fullycovered $FULLYCOVERED -"
  echo "$SHA noexec $NOEXEC -"
fi
