#!/bin/bash

INPUT=$1
OUTPUT=$2

>"$INPUT.pp"
for (( B=10; B<20; B++ )); do
  echo -n "$(($B-9)) " >> "$INPUT.pp"
  grep -v '#' $1|awk "BEGIN { FS=\",\" } ; { print \$$B }"|paste -sd+ |bc >> "$INPUT.pp"
done

gnuplot << EOF
  set term postscript eps enhanced
  set output "$OUTPUT.1.eps"
  set style fill solid border -1
  #set xrange [ -0.5 : ]
  set yrange [ 0 : ]
  set nokey

  set boxwidth 0.5

  plot "$INPUT.pp" using 2:xtic(1) with boxes

  !epstool --copy --bbox "$OUTPUT.1.eps" "$OUTPUT.eps"
  !epstopdf "$OUTPUT.eps" && rm "$OUTPUT.eps" "$OUTPUT.1.eps"
EOF

rm "$INPUT.pp"
