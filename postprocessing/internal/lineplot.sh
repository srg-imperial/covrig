#!/bin/bash

INPUT=$1
OUTPUT=$2
XLABEL=$(echo $XLABEL)
YLABEL=${4:-Revisions}
EXTRACMD=$5
GRAPHTYPE=${6:-standalone}

if [ -z "$XLABEL" ]; then
  XLABELCMD=
else
  XLABELCMD="set xlabel \"$XLABEL\""
fi

if [[ $GRAPHTYPE == "standalone" ]]; then
  CMD=gnuplot
  ARGS=
else
  CMD=cat
  ARGS="-"
fi

$CMD $ARGS >>$GRAPHTYPE << EOF
  set term postscript eps enhanced color
  set output "$OUTPUT.1.eps"
  $XLABELCMD
  set ylabel "$YLABEL"
  set xrange [ 0 : ]
  set noxtics
  set style line 1 lc rgb '#00B5E5' lt 1 lw 1 pt 1 ps 0.6

  $EXTRACMD

  plot "$INPUT" using 2 w points ls 1 notitle
  
  !epstool --copy --bbox "$OUTPUT.1.eps" "$OUTPUT.eps"
  !epstopdf "$OUTPUT.eps" && rm "$OUTPUT.eps" "$OUTPUT.1.eps"
EOF

