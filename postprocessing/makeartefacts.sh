#!/usr/bin/env bash

INPUTS=(data/Redis/Redis.csv data/Zeromq/Zeromq.csv data/Lighttpd/Lighttpd.csv data/Memcached/Memcached.csv data/Binutils/Binutils.csv data/Git/Git.csv)
OUTPUTS=(redis zeromq lighttpd memcached binutils git)

REVISIONS=250

declare -r GPELOC=tmp/multipleeloc
declare -r GPTLOC=tmp/multipletloc
declare -r GPCOV=tmp/multipletcov
declare -r CHURN=tmp/multiplechrn
declare -r ELTL=tmp/multipleeltl
declare -r ELTLZO=tmp/multipleeltlzo

mkdir -p graphs latex
rm -f $GPELOC $GPTLOC $GPCOV $CHURN $ELTL $ELTLZO

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

    $SCRIPT_DIR/grapheloc.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/eloc${OUTPUTS[$i]}" "$GPELOC"
    $SCRIPT_DIR/graphtloc.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/tloc${OUTPUTS[$i]}" "$GPTLOC"
    $SCRIPT_DIR/grapheloctloc.sh tmp/outptmp_${OUTPUTS[$i]} graphs/eltl${OUTPUTS[$i]} standard "$ELTL"
    $SCRIPT_DIR/grapheloctloc.sh tmp/outptmp_${OUTPUTS[$i]} graphs/etzo${OUTPUTS[$i]} zeroone "$ELTLZO"
    $SCRIPT_DIR/graphcoverage.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/covg${OUTPUTS[$i]}" "$GPCOV"
    $SCRIPT_DIR/graphchurn.sh "tmp/outptmp_${OUTPUTS[$i]}" "graphs/chrn${OUTPUTS[$i]}" "$CHURN"
    $SCRIPT_DIR/covsummary.sh --latex --prefix=${OUTPUTS[$i]} tmp/outptmp_${OUTPUTS[$i]} > latex/${OUTPUTS[$i]}.tex
  fi
done

#we only have bug coverage for memcached and zeromq
$SCRIPT_DIR/graphbugcoverage.sh repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ graphs/bugcoveragememcached
$SCRIPT_DIR/graphbugcoverage.sh repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ graphs/fixcoveragememcached fix

$SCRIPT_DIR/graphbugcoverage.sh repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ graphs/bugcoveragezeromq
$SCRIPT_DIR/graphbugcoverage.sh repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ graphs/fixcoveragezeromq fix

echo 'set term postscript eps enhanced' >multipleeloc.gp
echo 'set output "eloc.1.eps"' >> multipleeloc.gp
echo 'set multiplot layout 2, 3' >> multipleeloc.gp
echo 'set tmargin 2' >> multipleeloc.gp
egrep -v 'set term|set output|!eps' "$GPELOC" >>multipleeloc.gp
echo '!epstool --copy --bbox "eloc.1.eps" "eloc.eps"' >>multipleeloc.gp
echo '!epstopdf eloc.eps && mv eloc.pdf graphs/ && rm eloc.1.eps "eloc.eps"' >>multipleeloc.gp
gnuplot multipleeloc.gp

echo 'set term postscript eps enhanced' >multipletloc.gp
echo 'set output "tloc.1.eps"' >> multipletloc.gp
echo 'set multiplot layout 2, 3' >> multipletloc.gp
echo 'set tmargin 2' >> multipletloc.gp
egrep -v 'set term|set output|!eps' "$GPTLOC" >>multipletloc.gp
echo '!epstool --copy --bbox "tloc.1.eps" "tloc.eps"' >>multipletloc.gp
echo '!epstopdf tloc.eps && mv tloc.pdf graphs/ && rm tloc.1.eps "tloc.eps"' >>multipletloc.gp
gnuplot multipletloc.gp

echo 'set term postscript eps enhanced' >multiplecov.gp
echo 'set output "coverage.1.eps"' >> multiplecov.gp
echo 'set multiplot layout 2, 3' >> multiplecov.gp
echo 'set tmargin 2' >> multiplecov.gp
egrep -v 'set term|set output|!eps' "$GPCOV" >>multiplecov.gp
echo '!epstool --copy --bbox "coverage.1.eps" "coverage.eps"' >>multiplecov.gp
echo '!epstopdf coverage.eps && mv coverage.pdf graphs/ && rm coverage.1.eps "coverage.eps"' >>multiplecov.gp
gnuplot multiplecov.gp

echo 'set term postscript eps enhanced' >multiplechurn.gp
echo 'set output "churn.1.eps"' >> multiplechurn.gp
echo 'set multiplot layout 2, 3' >> multiplechurn.gp
echo 'set tmargin 2' >> multiplechurn.gp
egrep -v 'set term|set output|!eps' "$CHURN" >>multiplechurn.gp
echo '!epstool --copy --bbox "churn.1.eps" "churn.eps"' >>multiplechurn.gp
echo '!epstopdf churn.eps && mv churn.pdf graphs/ && rm churn.1.eps "churn.eps"' >>multiplechurn.gp
gnuplot multiplechurn.gp

echo 'set term postscript eps enhanced' >multipleeltl.gp
echo 'set output "eltl.1.eps"' >> multipleeltl.gp
echo 'set multiplot layout 3, 2' >> multipleeltl.gp
echo 'set tmargin 2' >> multipleeltl.gp
egrep -v 'set term|set output|!eps' "$ELTL" >>multipleeltl.gp
echo '!epstool --copy --bbox "eltl.1.eps" "eltl.eps"' >>multipleeltl.gp
echo '!epstopdf eltl.eps && mv eltl.pdf graphs/ && rm eltl.1.eps "eltl.eps"' >>multipleeltl.gp
gnuplot multipleeltl.gp

echo 'set term postscript eps enhanced' >multipleeltlzo.gp
echo 'set output "eltlzo.1.eps"' >> multipleeltlzo.gp
echo 'set multiplot layout 3, 2' >> multipleeltlzo.gp
echo 'set tmargin 2' >> multipleeltlzo.gp
egrep -v 'set term|set output|!eps' "$ELTLZO" >>multipleeltlzo.gp
echo '!epstool --copy --bbox "eltlzo.1.eps" "eltlzo.eps"' >>multipleeltlzo.gp
echo '!epstopdf eltlzo.eps && mv eltlzo.pdf graphs/ && rm eltlzo.1.eps "eltlzo.eps"' >>multipleeltlzo.gp
gnuplot multipleeltlzo.gp

rm -f tmp/outptmp_* multiple?loc.gp multiplecov.gp multiplechurn.gp multipleeltl*.gp
