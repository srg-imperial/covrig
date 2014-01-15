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
  set term postscript eps enhanced
  set output "$OUTPUT.1.eps"
  $XLABELCMD
  set ylabel "$YLABEL"
  set y2label "$Y2LABEL"
  set y2tics nomirror
  set ytics nomirror
  set xrange [ 0 : ]
  set noxtics
  set key left top
  $EXTRACMD

  plot "$INPUT" using 2 lc rgb "#4169E1" t "ELOC" w lines, \
       "$INPUT" using 3 lc rgb "#B22222" t "TLOC" w lines axes x1y2
  
  !epstool --copy --bbox "$OUTPUT.1.eps" "$OUTPUT.eps"
  !epstopdf "$OUTPUT.eps" && rm "$OUTPUT.eps" "$OUTPUT.1.eps"
EOF

