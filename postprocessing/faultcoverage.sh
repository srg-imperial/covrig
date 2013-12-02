#!/bin/bash

# script to determine wether bugs are in covered or uncovered code
# first argument is the target git repository
# second argument is the has (of a revisions which have been determined to be a fix)
# third argument is a folder which contains the coverage information for the revision
# in the format coverage-<sha>.tar.bz2

die () {
    echo >&2 "$@"
    exit 1
}
[ $# -eq 3 ] || die "Usage: $0 <git repo> <bug fixes rev> <cov info folder>"

REPO=$1
SHA=$2
COV=$3

# returns
#  0 executable and not covered
#  1 executable and covered
#  2 not executable
#  >2 an error has occurred
function is_covered () {
  local FILE=$1
  local LINE=$2
  local COVDIR=$3
  local SHA=$4
  local STATUS=5

  SSHA=${SHA:0:7}
  if [ -f $COVDIR/coverage-$SSHA.tar.bz2 ]; then
    if [ ! -f faultcov-tmp/coverage-$SSHA.tar.bz2 ]; then
      rm -rf faultcov-tmp
      mkdir -p faultcov-tmp && cp $COVDIR/coverage-$SSHA.tar.bz2 faultcov-tmp
      cd faultcov-tmp
      tar xjf coverage-$SSHA.tar.bz2
    else
      cd faultcov-tmp
    fi

    if [ ! -f total.info ]; then
      cd ..
      return 3
    fi
    RECORD=$( sed -n '\|SF:.*/'$FILE'|,/end_of_record/p' total.info |grep "^DA:$LINE," )
    if [[ "X$RECORD" == "X" ]]; then
      STATUS=2
    else
      if echo "$RECORD" | grep ",0$" >/dev/null; then
        STATUS=0
      else
        STATUS=1
      fi
    fi
    cd .. # && rm -rf faultcov-tmp
  fi
  return $STATUS
}

declare -r git_new_file_regex="\+\+\+ b/(.*)"
declare -r new_hunk_regex="@@.*\+([0-9]+),([0-9]+) @@"
declare -r new_hunk_def_regex="@@.*\+([0-9]+) @@"

PREVSHA=$( cd $REPO && git rev-parse $SHA~1 )
bIFS=$IFS
IFS=$'\n'
DIFF=( $(cd $REPO && git diff -b -U0 $SHA $SHA~1) )
IFS=$bIFS

TOTAL_NEW=0
TOTAL_NEW_UNCOVERED=0
CFILE=
COVSTATUS=0
FULLYCOVERED=1
NOEXEC=1

rm -rf faultcov-tmp
for line in "${DIFF[@]}"; do
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
        is_covered "$CFILE" $i $COV $PREVSHA
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
done

if [[ $COVSTATUS -lt 3 ]]; then
  echo "$SHA fullycovered $FULLYCOVERED -"
  echo "$SHA noexec $NOEXEC -"
fi
