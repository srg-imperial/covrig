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
  set key left top
  set style line 1 lc rgb '#00B5E5' lt 1 lw 1 pt 1 ps 0.5
  set style line 2 lc rgb '#CB2027' lt 2 lw 1 pt 2 ps 0.5

  set style line 3 lc rgb '#00B5E5' lt 1 lw 1.5 pt 1 ps 1
  set style line 4 lc rgb '#CB2027' lt 2 lw 1.5 pt 2 ps 1
  $EXTRACMD

  plot "$INPUT" using 2 notitle w points ls 1, \
       ""       using 3 notitle w points ls 2, \
       -1       t "Line cov" w points ls 3, \
       -1       t "Branch cov" w points ls 4
  
  !epstool --copy --bbox "$OUTPUT.1.eps" "$OUTPUT.eps"
  !epstopdf "$OUTPUT.eps" && rm "$OUTPUT.eps" "$OUTPUT.1.eps"
EOF

