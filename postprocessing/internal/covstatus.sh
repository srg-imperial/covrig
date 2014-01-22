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

# returns
#  0 x y executable and covered x out of y branches
#  1 x x not executable
#  3+ x x an error has occurred
function is_br_covered() {
  local FILE=$1
  local LINE=$2
  local COVDIR=$3
  local SHA=$4

  SSHA=${SHA:0:7}
  if [ -f $COVDIR/coverage-$SSHA.tar.bz2 ]; then
    if [ ! -f faultcov-tmp/coverage-$SSHA.tar.bz2 ]; then
      rm -rf faultcov-tmp
      mkdir -p faultcov-tmp && tar xjf $COVDIR/coverage-$SSHA.tar.bz2  -C faultcov-tmp
    fi
    cd faultcov-tmp

    if [ ! -f total.info ]; then
      cd ..
      echo "3 0 0"
      return
    fi
    RECORDCNT=$( sed -n '\|SF:.*/'$FILE'|,/end_of_record/p' total.info |grep "^BRDA:$LINE," |wc -l )
    if [[ $RECORDCNT -eq 0 ]]; then
      echo "1 0 0"
    else
      NOCOVRECORDCNT=$( sed -n '\|SF:.*/'$FILE'|,/end_of_record/p' total.info |grep '^BRDA:'$LINE',.*,[0-]$' |wc -l )
      echo "0 $((RECORDCNT-NOCOVRECORDCNT)) $NOCOVRECORDCNT"
    fi
    cd .. # && rm -rf faultcov-tmp
  else
    echo "3 0 0"
  fi
  return 0
}

