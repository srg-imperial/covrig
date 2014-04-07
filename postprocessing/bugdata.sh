#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

#we only look at bug coverage for memcached zeromq and redis
echo Redis fix
$SCRIPT_DIR/fixcoverage-multiple.sh --latex --prefix=redis repos/redis/ bugs/fixes-redis.simple data/Redis/ data/Redis/Redis.csv >latex/redis-bf.tex
echo Redis bug
$SCRIPT_DIR/faultcoverage-multiple.sh --latex --prefix=redis repos/redis/ bugs/fixes-redis.simple data/Redis/ data/Redis/Redis.csv >>latex/redis-bf.tex
echo Memcached fix
$SCRIPT_DIR/fixcoverage-multiple.sh --latex --prefix=memcached repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ data/Memcached/Memcached.csv >latex/memcached-bf.tex
echo Memcached bug
$SCRIPT_DIR/faultcoverage-multiple.sh --latex --prefix=memcached repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ data/Memcached/Memcached.csv >>latex/memcached-bf.tex
echo Zeromq fix
$SCRIPT_DIR/fixcoverage-multiple.sh --latex --prefix=zeromq repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ data/Zeromq/Zeromq.csv >latex/zeromq-bf.tex
echo Zeromq bug
$SCRIPT_DIR/faultcoverage-multiple.sh --latex --prefix=zeromq repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ data/Zeromq/Zeromq.csv >>latex/zeromq-bf.tex

#echo Redis fix br
#$SCRIPT_DIR/fixcoverage-multiple.sh --latex --prefix=redis repos/redis/ bugs/fixes-redis.simple data/Redis/ data/Redis/Redis.csv br >>latex/redis-bf.tex
#echo Redis bug br
#$SCRIPT_DIR/faultcoverage-multiple.sh --latex --prefix=redis repos/redis/ bugs/fixes-redis.simple data/Redis/ data/Redis/Redis.csv br >>latex/redis-bf.tex
#echo Memcached fix br
#$SCRIPT_DIR/fixcoverage-multiple.sh --latex --prefix=memcached repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ data/Memcached/Memcached.csv br >>latex/memcached-bf.tex
#echo Memcached bug br
#$SCRIPT_DIR/faultcoverage-multiple.sh --latex --prefix=memcached repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ data/Memcached/Memcached.csv br >>latex/memcached-bf.tex
#echo Zeromq fix br
#$SCRIPT_DIR/fixcoverage-multiple.sh --latex --prefix=zeromq repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ data/Zeromq/Zeromq.csv br >>latex/zeromq-bf.tex
#echo Zeromq bug br
#$SCRIPT_DIR/faultcoverage-multiple.sh --latex --prefix=zeromq repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ data/Zeromq/Zeromq.csv br >>latex/zeromq-bf.tex


#$SCRIPT_DIR/graphbugcoverage.sh repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ graphs/bugcoveragememcached bug
#$SCRIPT_DIR/graphbugcoverage.sh repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ graphs/fixcoveragememcached fix
#$SCRIPT_DIR/graphbugcoverage.sh repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ graphs/bugbrcoveragememcached bugbr
#$SCRIPT_DIR/graphbugcoverage.sh repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ graphs/fixbrcoveragememcached fixbr
#
#$SCRIPT_DIR/graphbugcoverage.sh repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ graphs/bugcoveragezeromq bug
#$SCRIPT_DIR/graphbugcoverage.sh repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ graphs/fixcoveragezeromq fix
#$SCRIPT_DIR/graphbugcoverage.sh repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ graphs/bugbrcoveragezeromq bugbr
#$SCRIPT_DIR/graphbugcoverage.sh repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ graphs/fixbrcoveragezeromq fixbr
#
#$SCRIPT_DIR/graphbugcoverage.sh repos/redis/ bugs/fixes-redis.simple data/Redis/ graphs/bugcoverageredis bug
#$SCRIPT_DIR/graphbugcoverage.sh repos/redis/ bugs/fixes-redis.simple data/Redis/ graphs/fixcoverageredis fix
#$SCRIPT_DIR/graphbugcoverage.sh repos/redis/ bugs/fixes-redis.simple data/Redis/ graphs/bugbrcoverageredis bugbr
#$SCRIPT_DIR/graphbugcoverage.sh repos/redis/ bugs/fixes-redis.simple data/Redis/ graphs/fixbrcoverageredis fixbr


