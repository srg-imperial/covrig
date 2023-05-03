#!/bin/bash

RELATIVE=0

while (( "$#" )); do
  case $1 in
    -r|--relative)
      RELATIVE=1
    ;;
    *)
      break;
    ;;
  esac
  shift
done

IGNOREREVS="#|compileError|EmptyCommit|NoCoverage"
INPUT=$1
OUTPUT=$2

>"$INPUT.pp"
COV=$(cat $1 |awk 'BEGIN { FS="," } ; { print $7 }'|egrep -v "$IGNOREREVS"|paste -sd+ |bc)
NCOV=$(cat $1 |awk 'BEGIN { FS="," } ; { print $8 }'|egrep -v "$IGNOREREVS"|paste -sd+ |bc)
ALL=$((COV+NCOV))

for (( B=10; B<20; B++ )); do
  echo -n "$(($B-9)) " >> "$INPUT.pp"
  ABSLCOV=$(egrep -v "$IGNOREREVS" $1|awk "BEGIN { FS=\",\" } ; { print \$$B }"|paste -sd+ |bc)
  if [[ $RELATIVE -eq 1 ]]; then
    ABSLCOV=$(echo "scale = 2
                    $ABSLCOV*100/$ALL"|bc)
  fi
  echo $ABSLCOV >> "$INPUT.pp"
done

gnuplot << EOF
  set term postscript eps enhanced color
  set output "$OUTPUT.1.eps"
  set style fill solid border -1
  #set xrange [ -0.5 : ]
  set yrange [ 0 : ]
  set nokey
  #set noxtics

  set boxwidth 0.5

  plot "$INPUT.pp" using 2:xtic(1) with boxes

  !epstool --copy --bbox "$OUTPUT.1.eps" "$OUTPUT.eps"
  !epstopdf "$OUTPUT.eps" && rm "$OUTPUT.eps" "$OUTPUT.1.eps"
EOF

rm "$INPUT.pp"
