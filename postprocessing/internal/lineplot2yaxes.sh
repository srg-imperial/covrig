#!/bin/bash

INPUT=$1
OUTPUT=$2
#XLABEL=${3:-Size}
XLABEL=$(echo $XLABEL)
YLABEL=${4:-Revisions}
Y2LABEL=${4:-Revisions}
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
  set y2label "$Y2LABEL"
  set y2tics nomirror
  set ytics nomirror 50
  set xrange [ 0 : ]
  set noxtics
  set key left top
  set style line 1 lc rgb '#00B5E5' lt 1 lw 2 pt 1 ps 1
  set style line 2 lc rgb '#CB2027' lt 2 lw 1 pt 2 ps 1
  $EXTRACMD

  plot "$INPUT" using 2 ls 1 t "Code" w lines, \
       "$INPUT" using 3 ls 2 t "Test" w lines axes x1y2
  
  !epstool --copy --bbox "$OUTPUT.1.eps" "$OUTPUT.eps"
  !epstopdf "$OUTPUT.eps" && rm "$OUTPUT.eps" "$OUTPUT.1.eps"
EOF

