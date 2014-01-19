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
  set term postscript eps enhanced
  set output "$OUTPUT.1.eps"
  $XLABELCMD
  set ylabel "$YLABEL"
  set xrange [ 0 : ]
  set noxtics
  set key left top
  set style line 1 lc rgb '#0060ad' lt 1 lw 1 pt 1 ps 0.5
  set style line 2 lc rgb '#dd181f' lt 2 lw 1 pt 2 ps 0.5
  $EXTRACMD

  plot "$INPUT" using 2 t "Line cov" w points ls 1, \
       ""       using 3 t "Br cov"   w points ls 2
  
  !epstool --copy --bbox "$OUTPUT.1.eps" "$OUTPUT.eps"
  !epstopdf "$OUTPUT.eps" && rm "$OUTPUT.eps" "$OUTPUT.1.eps"
EOF

