#!/usr/bin/env bash

INPUTS=(data/Binutils/Binutils.csv data/Git/Git.csv data/Lighttpd/Lighttpd.csv data/Memcached/Memcached.csv data/Redis/Redis.csv data/Zeromq/Zeromq.csv)
OUTPUTS=(Binutils Git Lighttpd Memcached Redis ZeroMQ)

REVISIONS=250

declare -r GPELOC=tmp/multipleeloc
declare -r GPTLOC=tmp/multipletloc
declare -r GPCOV=tmp/multiplecov
declare -r GPCOV2=tmp/multiplecov-lb
declare -r CHURN=tmp/multiplechrn
declare -r ELTL=tmp/multipleeltl
declare -r ELTLZO=tmp/multipleeltlzo
declare -r PCS=tmp/patchcovstacked
declare -r PTS=tmp/patchtypestacked

mkdir -p graphs latex tmp
rm -f $GPELOC $GPTLOC $GPCOV $GPCOV2 $CHURN $ELTL $ELTLZO $PCH $PCS $PTS

if [ ! -d data ]; then
  echo 'data folder must exist before running this script.'
  exit
fi

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
for ((i=0;i<${#INPUTS[@]};++i)); do
  if [ -f ${INPUTS[$i]} ]; then
    ACTUALREVS=$($SCRIPT_DIR/internal/goodtobad.sh ${INPUTS[$i]} $REVISIONS)
    tail -$ACTUALREVS ${INPUTS[$i]} > tmp/outptmp_${OUTPUTS[$i]}

    #script <input file> <output file>
    $SCRIPT_DIR/latentcoveragegraph.sh tmp/outptmp_${OUTPUTS[$i]} graphs/latent${OUTPUTS[$i]}
    $SCRIPT_DIR/latentcoveragegraph.sh --relative tmp/outptmp_${OUTPUTS[$i]} graphs/latentrel${OUTPUTS[$i]}
    $SCRIPT_DIR/patchcoverage.sh tmp/outptmp_${OUTPUTS[$i]} graphs/patchcov${OUTPUTS[$i]}
    $SCRIPT_DIR/grapheloc.sh tmp/outptmp_${OUTPUTS[$i]} graphs/eloc${OUTPUTS[$i]}
    $SCRIPT_DIR/graphtloc.sh tmp/outptmp_${OUTPUTS[$i]} graphs/tloc${OUTPUTS[$i]}
    $SCRIPT_DIR/grapheloctloc.sh tmp/outptmp_${OUTPUTS[$i]} graphs/eltl${OUTPUTS[$i]}
    $SCRIPT_DIR/grapheloctloc.sh tmp/outptmp_${OUTPUTS[$i]} graphs/etzo${OUTPUTS[$i]} zeroone
    $SCRIPT_DIR/graphcoverage.sh tmp/outptmp_${OUTPUTS[$i]} graphs/covg${OUTPUTS[$i]}
    $SCRIPT_DIR/graphchurn.sh tmp/outptmp_${OUTPUTS[$i]} graphs/chrn${OUTPUTS[$i]}
    $SCRIPT_DIR/graphpatchcoverage.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/pchg${OUTPUTS[$i]}" >>$PCS
    $SCRIPT_DIR/graphpatchtype.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/ptst${OUTPUTS[$i]}" >>$PTS

    $SCRIPT_DIR/grapheloc.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/eloc${OUTPUTS[$i]}" "$GPELOC"
    $SCRIPT_DIR/graphtloc.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/tloc${OUTPUTS[$i]}" "$GPTLOC"
    $SCRIPT_DIR/grapheloctloc.sh tmp/outptmp_${OUTPUTS[$i]} graphs/eltl${OUTPUTS[$i]} standard "$ELTL"
    $SCRIPT_DIR/grapheloctloc.sh tmp/outptmp_${OUTPUTS[$i]} graphs/etzo${OUTPUTS[$i]} zeroone "$ELTLZO"
    $SCRIPT_DIR/graphcoverage.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/covg${OUTPUTS[$i]}" "$GPCOV"
    $SCRIPT_DIR/graphchurn.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/chrn${OUTPUTS[$i]}" "$CHURN"
    $SCRIPT_DIR/covsummary.sh --latex --prefix=${OUTPUTS[$i]} tmp/outptmp_${OUTPUTS[$i]} > latex/${OUTPUTS[$i]}.tex
  fi
done

echo 'set term postscript eps enhanced color' >multipleeloc.gp
echo 'set output "eloc.1.eps"' >> multipleeloc.gp
echo 'set multiplot layout 2, 3' >> multipleeloc.gp
echo 'set tmargin 2' >> multipleeloc.gp
egrep -v 'set term|set output|!eps' "$GPELOC" >>multipleeloc.gp
echo '!epstool --copy --bbox "eloc.1.eps" "eloc.eps"' >>multipleeloc.gp
echo '!epstopdf eloc.eps && mv eloc.pdf graphs/ && rm eloc.1.eps "eloc.eps"' >>multipleeloc.gp
gnuplot multipleeloc.gp
#
echo 'set term postscript eps enhanced color' >multipletloc.gp
echo 'set output "tloc.1.eps"' >> multipletloc.gp
echo 'set multiplot layout 2, 3' >> multipletloc.gp
echo 'set tmargin 2' >> multipletloc.gp
egrep -v 'set term|set output|!eps' "$GPTLOC" >>multipletloc.gp
echo '!epstool --copy --bbox "tloc.1.eps" "tloc.eps"' >>multipletloc.gp
echo '!epstopdf tloc.eps && mv tloc.pdf graphs/ && rm tloc.1.eps "tloc.eps"' >>multipletloc.gp
gnuplot multipletloc.gp
#
echo 'set term postscript eps enhanced color' >multiplecov.gp
echo 'set output "coverage.1.eps"' >> multiplecov.gp
echo 'set multiplot layout 2, 3' >> multiplecov.gp
echo 'set tmargin 2' >> multiplecov.gp
egrep -v 'set term|set output|!eps' "$GPCOV" >>multiplecov.gp
echo '!epstool --copy --bbox "coverage.1.eps" "coverage.eps"' >>multiplecov.gp
echo '!epstopdf coverage.eps && mv coverage.pdf graphs/ && rm coverage.1.eps "coverage.eps"' >>multiplecov.gp
gnuplot multiplecov.gp

echo 'set term postscript eps enhanced color' >multiplecov.gp
echo 'set output "coverage-lb.1.eps"' >> multiplecov.gp
echo 'set multiplot layout 2, 3' >> multiplecov.gp
echo 'set tmargin 2' >> multiplecov.gp
egrep -v 'set term|set output|!eps' "$GPCOV2" >>multiplecov.gp
echo '!epstool --copy --bbox "coverage-lb.1.eps" "coverage-lb.eps"' >>multiplecov.gp
echo '!epstopdf coverage-lb.eps && mv coverage-lb.pdf graphs/ && rm coverage-lb.1.eps "coverage-lb.eps"' >>multiplecov.gp
gnuplot multiplecov.gp

echo 'set term postscript eps enhanced color' >multiplechurn.gp
echo 'set output "churn.1.eps"' >> multiplechurn.gp
echo 'set multiplot layout 2, 3' >> multiplechurn.gp
echo 'set tmargin 2' >> multiplechurn.gp
egrep -v 'set term|set output|!eps' "$CHURN" >>multiplechurn.gp
echo '!epstool --copy --bbox "churn.1.eps" "churn.eps"' >>multiplechurn.gp
echo '!epstopdf churn.eps && mv churn.pdf graphs/ && rm churn.1.eps "churn.eps"' >>multiplechurn.gp
gnuplot multiplechurn.gp
#
echo 'set term postscript eps enhanced color' >multipleeltl.gp
echo 'set output "eltl.1.eps"' >> multipleeltl.gp
echo 'set multiplot layout 3, 2' >> multipleeltl.gp
echo 'set tmargin 2' >> multipleeltl.gp
egrep -v 'set term|set output|!eps' "$ELTL" >>multipleeltl.gp
echo '!epstool --copy --bbox "eltl.1.eps" "eltl.eps"' >>multipleeltl.gp
echo '!epstopdf eltl.eps && mv eltl.pdf graphs/ && rm eltl.1.eps "eltl.eps"' >>multipleeltl.gp
gnuplot multipleeltl.gp
#
echo 'set term postscript eps enhanced color' >multipleeltlzo.gp
echo 'set output "eltlzo.1.eps"' >> multipleeltlzo.gp
echo 'set multiplot layout 3, 2' >> multipleeltlzo.gp
echo 'set tmargin 2' >> multipleeltlzo.gp
egrep -v 'set term|set output|!eps' "$ELTLZO" >>multipleeltlzo.gp
echo '!epstool --copy --bbox "eltlzo.1.eps" "eltlzo.eps"' >>multipleeltlzo.gp
echo '!epstopdf eltlzo.eps && mv eltlzo.pdf graphs/ && rm eltlzo.1.eps "eltlzo.eps"' >>multipleeltlzo.gp
gnuplot multipleeltlzo.gp

gnuplot << EOF
set term postscript eps enhanced color
set output "patchcovstack.1.eps"
set grid layerdefault   linetype 0 linewidth 1.000,  linetype 0 linewidth 1.000
set border 3 front linetype -1 linewidth 1.000
set key outside right top vertical Left reverse invert noenhanced autotitles nobox
set style data histogram
set style histogram rowstacked
set style fill solid 1.00 border -1
set style line 1 lt 1 lc rgb "#BC2222"
set style line 2 lt 1 lc rgb "#FFB90F"
set style line 3 lt 1 lc rgb "#CAFF70"
set style line 4 lt 1 lc rgb "#4D9B00"
set style line 5 lt 1 lc rgb "#222222"

set boxwidth 0.7 relative

#plot "$PCS" u (\$2+\$3) t "[0%,     25%]" ls 1, '' u 4 t "(25%,   50%]" ls 2, '' u 5 t "(50%,   75%]" ls 3, '' u 6:xticlabels(1) t "(75%, 100%]" ls 4
plot "$PCS" u 2 t '' ls 5, '' u 3 t "[0%,     25%]" ls 1, '' u 4 t "(25%,   50%]" ls 2, '' u 5 t "(50%,   75%]" ls 3, '' u 6:xticlabels(1) t "(75%, 100%]" ls 4

!epstool --copy --bbox "patchcovstack.1.eps" "patchcovstack.eps"
!epstopdf "patchcovstack.eps" && mv patchcovstack.pdf graphs/ && rm "patchcovstack.eps" "patchcovstack.1.eps"
EOF

gnuplot << EOF
set term postscript eps enhanced color
set output "patchtypestacked.1.eps"
set xtics nomirror
set grid y linetype 0 linewidth 1.000,  linetype 0 linewidth 1.000
set border 3 front linetype -1 linewidth 1.000
set key outside right top vertical Left reverse invert noenhanced autotitles nobox
set style data histogram
set style histogram rowstacked
set style fill solid 1.00 border -1
set style line 1 lt 1 lc rgb "#BD2121"
set style line 2 lt 1 lc rgb "#BD3DFF"
set style line 3 lt 1 lc rgb "#6394ED"
set style line 4 lt 1 lc rgb "#EDEDED"

set boxwidth 0.7 relative

plot "$PTS" u 2 t "Code only" ls 1, '' u 3 t "Code+Test" ls 2, '' u 4 t "Test only" ls 3, '' u 5:xticlabels(1) t "Other" ls 4

!epstool --copy --bbox "patchtypestacked.1.eps" "patchtypestacked.eps"
!epstopdf "patchtypestacked.eps" && mv patchtypestacked.pdf graphs/ && rm "patchtypestacked.eps" "patchtypestacked.1.eps"
EOF


rm -f tmp/outptmp_* multiple?loc.gp multiplecov.gp multiplechurn.gp multipleeltl*.gp

echo Getting bug and fix data...
./postprocessing/bugdata.sh >/dev/null
