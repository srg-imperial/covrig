#!/bin/bash

echo Redis fix
./postprocessing/fixcoverage-multiple.sh --latex --prefix=redis repos/redis/ bugs/fixes-redis.simple data/Redis/ data/Redis/Redis.csv >latex/redis-bf.tex
echo Redis bug
./postprocessing/faultcoverage-multiple.sh --latex --prefix=redis repos/redis/ bugs/fixes-redis.simple data/Redis/ data/Redis/Redis.csv >>latex/redis-bf.tex
echo Memcached fix
./postprocessing/fixcoverage-multiple.sh --latex --prefix=memcached repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ data/Memcached/Memcached.csv >latex/memcached-bf.tex
echo Memcached bug
./postprocessing/faultcoverage-multiple.sh --latex --prefix=memcached repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ data/Memcached/Memcached.csv >>latex/memcached-bf.tex
echo Zeromq fix
./postprocessing/fixcoverage-multiple.sh --latex --prefix=zeromq repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ data/Zeromq/Zeromq.csv >latex/zeromq-bf.tex
echo Zeromq bug
./postprocessing/faultcoverage-multiple.sh --latex --prefix=zeromq repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ data/Zeromq/Zeromq.csv >>latex/zeromq-bf.tex

echo Redis fix br
./postprocessing/fixcoverage-multiple.sh --latex --prefix=redis repos/redis/ bugs/fixes-redis.simple data/Redis/ data/Redis/Redis.csv br >>latex/redis-bf.tex
echo Redis bug br
./postprocessing/faultcoverage-multiple.sh --latex --prefix=redis repos/redis/ bugs/fixes-redis.simple data/Redis/ data/Redis/Redis.csv br >>latex/redis-bf.tex
echo Memcached fix br
./postprocessing/fixcoverage-multiple.sh --latex --prefix=memcached repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ data/Memcached/Memcached.csv br >>latex/memcached-bf.tex
echo Memcached bug br
./postprocessing/faultcoverage-multiple.sh --latex --prefix=memcached repos/memcached/ bugs/fixes-memcached.simple data/Memcached/ data/Memcached/Memcached.csv br >>latex/memcached-bf.tex
echo Zeromq fix br
./postprocessing/fixcoverage-multiple.sh --latex --prefix=zeromq repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ data/Zeromq/Zeromq.csv br >>latex/zeromq-bf.tex
echo Zeromq bug br
./postprocessing/faultcoverage-multiple.sh --latex --prefix=zeromq repos/zeromq/ bugs/fixes-zeromq.simple data/Zeromq/ data/Zeromq/Zeromq.csv br >>latex/zeromq-bf.tex
