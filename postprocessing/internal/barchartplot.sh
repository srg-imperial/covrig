#!/bin/bash

INPUT=$1
OUTPUT=$2
FIELD=$3
BINWIDTH=${4:-5}
XLABEL=${5:-Size}
XLABEL=$(echo $XLABEL)
YLABEL=${6:-Revisions}
EXTRACMD=$7

if [[ $BINWIDTH -eq 1 ]]; then
  BOXWIDTH=0.8
else
  BOXWIDTH=$(( BINWIDTH -1 ))
fi

if [ -z "$XLABEL" ]; then
  XLABELCMD=
else
  XLABELCMD="set xlabel \"$XLABEL\""
fi

gnuplot << EOF
  set term postscript eps enhanced color
  set style histogram rowstacked
  set style data histograms
  set output "$OUTPUT.1.eps"
  $XLABELCMD
  set ylabel "$YLABEL"
  set style fill solid border
  #set style line 1 lt 1 lc rgb "#666666"  #"#00BFFF"
  set xrange [ 0 : ]
  set yrange [ 0 : 200 ]
  set noxtics
  #set nokey
  $EXTRACMD

  set boxwidth $BOXWIDTH

  plot "$INPUT" using 2 lt 1 lc rgb "#666666" t "Covered", '' u 3 lt 1 lc rgb "#990000" t "Not Covered"
  
  !epstool --copy --bbox "$OUTPUT.1.eps" "$OUTPUT.eps"
  !epstopdf "$OUTPUT.eps" && rm "$OUTPUT.eps" "$OUTPUT.1.eps"
EOF

