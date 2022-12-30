#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

REPO=$1
REVISIONS=$2
COVDIR=$3
OUTPUT=$4
BUGORFIX=${5:-bug}
TMPDATA="revcoverage.pp"

>$TMPDATA

for SHA in $(sort -u $REVISIONS); do
  if [[ "X$BUGORFIX" = "Xbug" ]]; then
    $SCRIPT_DIR/faultcoverage.sh $REPO $SHA $COVDIR > tmpfixcov
  elif [[ "X$BUGORFIX" = "Xfix" ]]; then
    $SCRIPT_DIR/fixcoverage.sh $REPO $SHA $COVDIR > tmpfixcov
  elif [[ "X$BUGORFIX" = "Xbugbr" ]]; then
    $SCRIPT_DIR/faultcoverage-br.sh $REPO $SHA $COVDIR > tmpfixcov
  elif [[ "X$BUGORFIX" = "Xfixbr" ]]; then
    $SCRIPT_DIR/fixcoverage-br.sh $REPO $SHA $COVDIR > tmpfixcov
  else
    echo "Unknown graph type: $BUGORFIX"
    exit 1
  fi

  COV=$(grep '1$' tmpfixcov | wc -l)
  NOTCOV=$(grep '0$' tmpfixcov | wc -l)
  if [[ "$COV" -gt 0 || "$NOTCOV" -gt 0 ]]; then
    PCOV=$(echo "scale = 2
                 $COV*100/($COV+$NOTCOV)"|bc)
    echo $PCOV $COV $NOTCOV >> $TMPDATA
  fi
done

gnuplot << EOF
  set term postscript eps enhanced color
  set output "$OUTPUT.1.eps"
  set style fill solid border -1
  set yrange [ 0 : 100 ]
  set nokey
  set noxtics

  set boxwidth 0.5

  plot "$TMPDATA" u 1 with boxes

  !epstool --copy --bbox "$OUTPUT.1.eps" "$OUTPUT.eps"
  !epstopdf "$OUTPUT.eps" && rm "$OUTPUT.eps" "$OUTPUT.1.eps"
EOF

gnuplot << EOF
  set term postscript eps enhanced color
  set output "$OUTPUT-linelevel.1.eps"
  set style data histograms
  set style histogram rowstacked
  set style fill pattern 3 border
  set style line 1 lt 1 lc rgb "#666666"  #"#00BFFF"

  set noxtics

  set boxwidth 0.5

  plot "$TMPDATA" u 2 ls 1 t "Covered", "" u 3 ls 1 t "Not covered"

  !epstool --copy --bbox "$OUTPUT-linelevel.1.eps" "$OUTPUT-linelevel.eps"
  !epstopdf "$OUTPUT-linelevel.eps" && rm "$OUTPUT-linelevel.eps" "$OUTPUT-linelevel.1.eps"
EOF


rm "$TMPDATA" tmpfixcov
