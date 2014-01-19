#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
INITIAL_DIR="$(pwd)"

die () {
    echo >&2 "$@"
    exit 1
}

LATEX=0
VARPREFIX="program"

while (( "$#" )); do
  case $1 in
    -l|--latex)
      LATEX=1
    ;;
    -p=*|--prefix=*)
      VARPREFIX="${1#*=}"
    ;;
    *)
      break;
    ;;
  esac
  shift
done

[ $# -eq 2 ] || [ $# -eq 1 ] || die "Usage: $0 filename [count]"

if [ $# -eq 2 ]; then
  ACTUAL_LINES=$($SCRIPT_DIR/internal/goodtobad.sh "$1" "$2")
  tail -$ACTUAL_LINES "$1" >process.partial 2>/dev/null || die "Invalid arguments"
  set -- "process.partial"
fi

IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"

FIRSTREV=$(grep -v '#' $1|head -1|awk 'BEGIN { FS="," } ; { print $1}')
LASTREV=$(tail -1 $1|awk 'BEGIN { FS="," } ; { print $1}')
FIRSTREVDATE="Unknown"
LASTREVDATE="Unknown"

SELECTCODEFILE="awk 'BEGIN { FS=\",\" } ; { if (\$25 > 0) print \$0 }'"
SELECTTESTFILE="awk 'BEGIN { FS=\",\" } ; { if (\$26 > 0) print \$0 }'"
SELECTACTUALCODE="awk 'BEGIN { FS=\",\" } ; { if (\$7 > 0 || \$8 > 0) print \$0 }'"
SELECTACTUALCODEORTEST="awk 'BEGIN { FS=\",\" } ; { if (\$7 > 0 || \$8 > 0 || \$26 > 0) print \$0 }'"
N2DIGITS='egrep -o "[0-9]+([.][0-9][0-9]?)?" |head -1'

#find the dates using brute force
for DIR in repos/*; do
  cd $DIR
  if git rev-parse $FIRSTREV &>/dev/null && git rev-parse $LASTREV &>/dev/null; then
    FIRSTREVDATE=$(git show --pretty=%ci $FIRSTREV|head -1)
    LASTREVDATE=$(git show --pretty=%ci $LASTREV|head -1)
    break
  fi
  cd ../..
done

cd "$INITIAL_DIR"
mkdir -p tmp

FRS=$(date -d "$FIRSTREVDATE" +%s)
LRS=$(date -d "$LASTREVDATE" +%s)
MOS=$(( ($LRS - $FRS) / (3600*24*30) ))
if [[ $LATEX -eq 1 ]]; then
  if [[ "$VARPREFIX" == "program" ]]; then
    echo "%% Warning: --prefix not given for latex output"
  fi
  ACTUALREVS=$(egrep -v "$IGNOREREVS" $1| eval $SELECTACTUALCODEORTEST |wc -l)

  echo "%% $VARPREFIX: $ACTUALREVS actual revisions ($FIRSTREV - $LASTREV)"
  
  echo "\\newcommand{\\${VARPREFIX}Revs}[0]{$ACTUALREVS\\xspace}"
  
  echo "\\newcommand{\\${VARPREFIX}Timespan}[0]{$MOS\\xspace}"

  LASTSIZE=$(egrep -v "$IGNOREREVS" $1|tail -1 |awk 'BEGIN { FS="," } ; { print $2 }')
  printf "\\\\newcommand{\\\\${VARPREFIX}Size}[0]{%'d\\\\xspace}\\n" $LASTSIZE

  LASTTSIZE=$(egrep -v "$IGNOREREVS" $1|tail -1|awk 'BEGIN { FS="," } ; { print $4 }')
  printf "\\\\newcommand{\\\\${VARPREFIX}Tsize}[0]{%'d\\\\xspace}\\n" $LASTTSIZE

  FIRSTSIZE=$(egrep -v "$IGNOREREVS" $1|head -1|awk 'BEGIN { FS="," } ; { print $2 }')
  DELTAELOC=$(($LASTSIZE - $FIRSTSIZE))
  printf "\\\\newcommand{\\\\${VARPREFIX}DeltaSize}[0]{%'d\\\\xspace}\\n" $DELTAELOC

  COVLINES=$(egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $7 }'|paste -sd+ |bc)
  printf "\\\\newcommand{\\\\${VARPREFIX}CovLines}[0]{%'d\\\\xspace}\\n" $COVLINES

  UNCOVLINES=$(egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $8 }'|paste -sd+ |bc)
  printf "\\\\newcommand{\\\\${VARPREFIX}UncovLines}[0]{%'d\\\\xspace}\\n" $UNCOVLINES
 
  printf "\\\\newcommand{\\\\${VARPREFIX}PatchTotal}[0]{%'d\\\\xspace}\\n" $((UNCOVLINES+COVLINES))

  INITIALCOVERAGE=$(grep -v '#' $1|head -1|awk 'BEGIN { FS="," } ; { print $3*100/$2}'|eval $N2DIGITS)
  echo "\\newcommand{\\${VARPREFIX}InitialCoverage}[0]{$INITIALCOVERAGE\\xspace}"
  FINALCOVERAGE=$(tail -1 $1|awk 'BEGIN { FS="," } ; { print $3*100/$2}'|eval $N2DIGITS)
  echo "\\newcommand{\\${VARPREFIX}FinalCoverage}[0]{$FINALCOVERAGE\\xspace}"

  TRANSIENTCOMPILEERRORS=$(egrep 'compileError|NoCoverage' $1|wc -l)
  echo "\\newcommand{\\${VARPREFIX}TransientCompErrs}[0]{$TRANSIENTCOMPILEERRORS\\xspace}"

  TRANSIENTTESTERRORS=$(cat $1 | eval $SELECTACTUALCODEORTEST |egrep 'SomeTestFailed' |wc -l)
  echo "\\newcommand{\\${VARPREFIX}TransientTestErrs}[0]{$TRANSIENTTESTERRORS\\xspace}"

  TRANSIENTTESTTIMEOUTS=$(cat $1 | eval $SELECTACTUALCODEORTEST |egrep 'TimedOut' |wc -l)
  echo "\\newcommand{\\${VARPREFIX}TransientTestTimeouts}[0]{$TRANSIENTTESTTIMEOUTS\\xspace}"

  ALLOK=$(cat $1 | eval $SELECTACTUALCODEORTEST |egrep 'OK' |wc -l)
  echo "\\newcommand{\\${VARPREFIX}OK}[0]{$ALLOK\\xspace}"

  MERGES=$(egrep -v "$IGNOREREVS" $1 |grep ',True'|wc -l)
  echo "\\newcommand{\\${VARPREFIX}Merges}[0]{$MERGES\\xspace}"
  echo

  ONLYEXECUTABLE=$(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if (($7 > 0 || $8 > 0) && $26 == 0) print 1 }'|wc -l)
  ONLYTEST=$(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($7 == 0 && $8 == 0 && $26 > 0) print 1 }'|wc -l)
  TESTANDEXECUTABLE=$(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if (($7 > 0 || $8 > 0) && $26 > 0) print 1 }'|wc -l)
  echo "\\newcommand{\\${VARPREFIX}OnlyTestRevs}[0]{$ONLYTEST\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}OnlyExecutableRevs}[0]{$ONLYEXECUTABLE\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}TestAndExecutableRevs}[0]{$TESTANDEXECUTABLE\\xspace}"

  REVISIONS=$(egrep -v "$IGNOREREVS" $1|wc -l)
  printf "\\\\newcommand{\\\\${VARPREFIX}NoTestNoExecutableRevs}[0]{%'d\\\\xspace}" $(($REVISIONS-$ONLYEXECUTABLE-$ONLYTEST-$TESTANDEXECUTABLE))

  echo

  STATVARNAMES=(Patch HunkZero eHunkZero HunkThree eHunkThree)
  STATVARCOLS=(\$7+\$8 \$22 \$23 \$27 \$28)

  #NB: these are computed only for revisions which add executable code
  for ((i=0;i<${#STATVARNAMES[@]};++i)); do
    egrep -v "$IGNOREREVS" $1 |eval $SELECTACTUALCODE | awk "BEGIN { FS=\",\" } ; { print ${STATVARCOLS[$i]} }"|sort -n > tmp/patchcnt
    PATCHAVG=$(cat tmp/patchcnt | $SCRIPT_DIR/statistics.pl|egrep -o "mean is [0-9.]+"|eval $N2DIGITS )
    PATCHMEDIAN=$(cat tmp/patchcnt | $SCRIPT_DIR/statistics.pl|egrep -o "median is [0-9.]+"|eval $N2DIGITS )
    PATCHMODE=$(cat tmp/patchcnt | $SCRIPT_DIR/statistics.pl|egrep -o "mode is [0-9.]+"|eval $N2DIGITS )
    PATCHSTDEV=$(cat tmp/patchcnt | $SCRIPT_DIR/statistics.pl|egrep -o "stdev is [0-9.]+"|eval $N2DIGITS )
    echo "\\newcommand{\\${VARPREFIX}${STATVARNAMES[$i]}Average}[0]{$PATCHAVG\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}${STATVARNAMES[$i]}Median}[0]{$PATCHMEDIAN\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}${STATVARNAMES[$i]}Mode}[0]{$PATCHMODE\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}${STATVARNAMES[$i]}Stdev}[0]{$PATCHSTDEV\\xspace}"
    echo
  done

  STATVARNAMES=(Coverage BranchCoverage)
  STATVARCOLS=(\$3*100/\$2 \$31*100/\$30)
  for ((i=0;i<${#STATVARNAMES[@]};++i)); do
    egrep -v "$IGNOREREVS" $1 | awk "BEGIN { FS=\",\" } ; { if (NF < 30 || \$30 > 0) { print ${STATVARCOLS[$i]} } else { print 0 } }"|sort -n > tmp/patchcnt
    PATCHAVG=$(cat tmp/patchcnt | $SCRIPT_DIR/statistics.pl|egrep -o "mean is [0-9.]+"|eval $N2DIGITS )
    PATCHMEDIAN=$(cat tmp/patchcnt | $SCRIPT_DIR/statistics.pl|egrep -o "median is [0-9.]+"|eval $N2DIGITS )
    PATCHMODE=$(cat tmp/patchcnt | $SCRIPT_DIR/statistics.pl|egrep -o "mode is [0-9.]+"|eval $N2DIGITS )
    PATCHSTDEV=$(cat tmp/patchcnt | $SCRIPT_DIR/statistics.pl|egrep -o "stdev is [0-9.]+"|eval $N2DIGITS )
    echo "\\newcommand{\\${VARPREFIX}${STATVARNAMES[$i]}Average}[0]{$PATCHAVG\\%\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}${STATVARNAMES[$i]}Median}[0]{$PATCHMEDIAN\\%\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}${STATVARNAMES[$i]}Mode}[0]{$PATCHMODE\\%\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}${STATVARNAMES[$i]}Stdev}[0]{${PATCHSTDEV}pp\\xspace}"
    echo
  done

  declare -a BUCKETS
  BUCKETS[1]=0
  BUCKETS[2]=10
  BUCKETS[3]=100
  BUCKETS[4]=100000

  #LaTeX doesn't allow digits in command names
  declare -a BUCKETNAMES
  BUCKETNAMES[1]="Zero"
  BUCKETNAMES[2]="Ten"
  BUCKETNAMES[3]="Hundred"
  BUCKETNAMES[4]="NA"
  for BUCKETIDX in 0 1 2 3; do
    if [[ $BUCKETIDX -eq 0 ]]; then
      #special case. get overall stats
      AWKSCRIPT="BEGIN { FS=\",\" } ; {
                  if (\$7+\$8 > 0) {
                    print \$7/(\$7+\$8)
                  }
                }"
    else
      AWKSCRIPT="BEGIN { FS=\",\" } ; {
                  if (\$7+\$8 >  ${BUCKETS[$BUCKETIDX]} &&
                      \$7+\$8 <= ${BUCKETS[$((BUCKETIDX+1))]}) {
                    print \$7/(\$7+\$8)
                  }
                }"
    fi
    BUCKETENTRIES=$(egrep -v "$IGNOREREVS" $1 |awk "$AWKSCRIPT" | wc -l);
    if [[ $BUCKETENTRIES -gt 0 ]]; then
      PATCHCOVAVG=$(egrep -v "$IGNOREREVS" $1 |awk "$AWKSCRIPT"|sort -n | $SCRIPT_DIR/statistics.pl|egrep -o "mean is [0-9.]+"|eval $N2DIGITS)
      PATCHCOVAVG=$(printf "%.0f\\%%" $(echo "$PATCHCOVAVG * 100"|bc))
      PATCHCOVMEDIAN=$(egrep -v "$IGNOREREVS" $1 |awk "$AWKSCRIPT"|sort -n | $SCRIPT_DIR/statistics.pl|egrep -o "median is [0-9.]+"|eval $N2DIGITS)
      PATCHCOVMEDIAN=$(printf "%.0f\\%%" $(echo "$PATCHCOVMEDIAN * 100"|bc))
      #this will fail if the mode has multiple values
      PATCHCOVMODE=$(egrep -v "$IGNOREREVS" $1 |awk "$AWKSCRIPT"|sort -n | $SCRIPT_DIR/statistics.pl|egrep -o "mode is [0-9.]+"|eval $N2DIGITS)
      PATCHCOVSTDEV=$(egrep -v "$IGNOREREVS" $1 |awk "$AWKSCRIPT"|sort -n | $SCRIPT_DIR/statistics.pl|egrep -o "stdev is [0-9.]+"|eval $N2DIGITS)
      PATCHCOVSTDEV=$(printf "%.0fpp" $(echo "$PATCHCOVSTDEV * 100"|bc))
    else
      PATCHCOVAVG="N/A"
      PATCHCOVMEDIAN="N/A"
      PATCHCOVMODE="N/A"
      PATCHCOVSTDEV="N/A"
    fi
    echo "\\newcommand{\\${VARPREFIX}PatchCovEntries${BUCKETNAMES[$BUCKETIDX]}}[0]{$BUCKETENTRIES\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}PatchCovAverage${BUCKETNAMES[$BUCKETIDX]}}[0]{$PATCHCOVAVG\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}PatchCovMedian${BUCKETNAMES[$BUCKETIDX]}}[0]{$PATCHCOVMEDIAN\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}PatchCovMode${BUCKETNAMES[$BUCKETIDX]}}[0]{$PATCHCOVMODE\\xspace}"
    echo "\\newcommand{\\${VARPREFIX}PatchCovStdev${BUCKETNAMES[$BUCKETIDX]}}[0]{$PATCHCOVSTDEV\\xspace}"
  
    echo
  done

  LATENT1=$(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $10 }'|paste -sd+ |bc)
  LATENT1=$(echo "scale=1; $LATENT1*100/($COVLINES+$UNCOVLINES)"|bc)"\\%"
  LATENT5=$(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $14 }'|paste -sd+ |bc)
  LATENT5=$(echo "scale=1; $LATENT5*100/($COVLINES+$UNCOVLINES)"|bc)"\\%"
  LATENT10=$(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $19 }'|paste -sd+ |bc)
  LATENT10=$(echo "scale=1; $LATENT10*100/($COVLINES+$UNCOVLINES)"|bc)"\\%"

  echo "\\newcommand{\\${VARPREFIX}LatentOne}[0]{$LATENT1\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}LatentFive}[0]{$LATENT5\\xspace}"
  echo "\\newcommand{\\${VARPREFIX}LatentTen}[0]{$LATENT10\\xspace}"

else
  echo "Looking at revisions $FIRSTREV - $LASTREV ($MOS months: $FIRSTREVDATE - $LASTREVDATE)"
  
  
  echo -n "+++Empty revisions: "
  grep EmptyCommit $1|wc -l
  echo
  
  echo -n "+++Compile errors: "
  grep compileError $1|wc -l
  echo
  
  echo -n "+++Good revisions: "
  egrep -v "$IGNOREREVS" $1|wc -l
  echo
  
  echo -n "+++Test failures: "
  grep SomeTestFailed $1|wc -l
  echo
  
  echo -n "+++Merges: "
  egrep -v -e "$IGNOREREVS" $1 |grep ',True'|wc -l
  echo
  
  echo -n "+++Added/modified ELOC: "
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $7+$8 }'|paste -sd+ |bc
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $7+$8 }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo -n "+++Covered lines: "
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $7 }'|paste -sd+ |bc
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $7 }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo -n "+++Not covered lines: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $8 }'|paste -sd+ |bc
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $8 }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo "+++Patch coverage: "
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { if ($7+$8 != 0) { print $7/($7+$8) } }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo

  echo -n "+++Affected files: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $24 }'|paste -sd+ |bc
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $24 }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo -n "+++Affected executable files: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $25 }'|paste -sd+ |bc
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $25 }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo -n "+++Revisions affecting 0 files: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $24 }'|grep '^0$'|wc -l
  echo
  
  echo -n "+++Revisions affecting only test files: "
  #egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($24 == $26 && $26 > 0) print 1 }'|wc -l
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($7 == 0 && $8 == 0 && $26 > 0) print 1 }'|wc -l
  echo
  
  echo -n "+++Revisions affecting only executable files: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($24 == $25 && $25 > 0) print 1 }'|wc -l
  echo
  
  echo -n "+++Revisions affecting executable or test files: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($25 > 0 || $26 > 0) print 1 }'|wc -l
  echo
  
  echo -n "+++Revisions adding executable code or affecting test files: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($7 > 0 || $8 > 0 || $26 > 0) print 1 }'|wc -l
  echo
  
  echo -n "+++Revisions affecting only test files without increasing coverage: "
  >tmp/summary
  for R in $(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($24 == $26) { print $1 } }')
  do
    grep -B1 $R $1|awk 'BEGIN { FS="," } ; { print $3 }' | { read -r first; read -r second
      if [[ $first == $second ]]; then
        echo $R >> tmp/summary
      fi
    }
  done
  cat tmp/summary | wc -l
  cat tmp/summary
  echo
  
  echo -n "+++Revisions affecting only test files decreasing coverage: "
  >tmp/summary
  for R in $(egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($24 == $26) { print $1 } }')
  do
    grep -B1 $R $1|awk 'BEGIN { FS="," } ; { print $3 }' | { read -r first; read -r second
      if [[ $first -gt $second ]]; then
        echo $R $(($first - $second)) >> tmp/summary
      fi
    }
  done
  cat tmp/summary |wc -l
  cat tmp/summary
  echo
  
  echo -n "+++Hunks: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $22 }'|paste -sd+ |bc
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $22 }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo -n "+++Hunks w/ context 3: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $27 }'|paste -sd+ |bc
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $27 }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo -n "+++Executable hunks: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $23 }'|paste -sd+ |bc
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $23 }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo -n "+++Executable hunks w/ context 3: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $28 }'|paste -sd+ |bc
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $28 }'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  for (( B=10; B<20; B++ )); do
    echo -n "Covered lines from previous $(($B-9)) patches: "
    egrep -v "$IGNOREREVS" $1|awk "BEGIN { FS=\",\" } ; { print \$$B }"|paste -sd+ |bc
  done
  echo
  
  echo -n "+++Revisions contribuiting to latent patch coverage@1: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $10 }'|grep -v '^0$'|wc -l
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $10 }'|grep -v '^0$'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo -n "+++Revisions contribuiting to latent patch coverage@10: "
  egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { print $19 }'|grep -v '^0$'|wc -l
  egrep -v "$IGNOREREVS" $1 |awk 'BEGIN { FS="," } ; { print $19 }'|grep -v '^0$'|sort -n | $SCRIPT_DIR/statistics.pl
  echo
  
  echo -n "+++Contribuition of revisions containing only test files to latent patch coverage@10: "
  REVS=$( egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($19 > 0 && $24-$26 == 0) print $19 }'|wc -l )
  LCOV=$( egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($19 > 0 && $24-$26 == 0) print $19 }'|paste -sd+|bc )
  echo "$REVS revisions = $LCOV lines"
  
  echo -n "+++Contribuition of revisions containing some test files to latent patch coverage@10: "
  REVS=$( egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($19 > 0 && $26 > 0 && $24 > $26) print $19 }'|wc -l )
  LCOV=$( egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($19 > 0 && $26 > 0 && $24 > $26) print $19 }'|paste -sd+|bc )
  echo "$REVS revisions = $LCOV lines"
  
  echo -n "+++Contribuition of revisions containing no test files to latent patch coverage@10: "
  REVS=$( egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($19 > 0 && $26 == 0) print $19 }'|wc -l )
  LCOV=$( egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($19 > 0 && $26 == 0) print $19 }'|paste -sd+|bc )
  ACTUAL=$( egrep -v "$IGNOREREVS" $1|awk 'BEGIN { FS="," } ; { if ($19 > 0 && $26 == 0) print $1 }' |tr '\r\n' ' ')
  echo "$REVS revisions = $LCOV lines ($ACTUAL)"
fi
rm -f tmp/summary process.partial
