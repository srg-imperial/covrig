#!/bin/bash

./postprocessing/nondet.sh --only-ok --latex --prefix=binutils /data/analytics-data/vmdata/Binutils1/Binutils.csv /data/analytics-data/vmdata/Binutils1 /data/analytics-data/vmdata/Binutils2 /data/analytics-data/vmdata/Binutils3 /data/analytics-data/vmdata/Binutils4 /data/analytics-data/vmdata/Binutils5 >latex/binutils-nondet.tex

./postprocessing/nondet.sh --only-ok --latex --prefix=zeromq /data/analytics-data/vmdata/Zeromq1/Zeromq.csv /data/analytics-data/vmdata/Zeromq1 /data/analytics-data/vmdata/Zeromq2 /data/analytics-data/vmdata/Zeromq3 /data/analytics-data/vmdata/Zeromq4 /data/analytics-data/vmdata/Zeromq5 >latex/zeromq-nondet.tex

./postprocessing/nondet.sh --only-ok --latex --prefix=lighttpd /data/analytics-data/vmdata/Lighttpd1/Lighttpd.csv /data/analytics-data/vmdata/Lighttpd1 /data/analytics-data/vmdata/Lighttpd2 /data/analytics-data/vmdata/Lighttpd3 /data/analytics-data/vmdata/Lighttpd4 /data/analytics-data/vmdata/Lighttpd5 >latex/lighttpd-nondet.tex

./postprocessing/nondet.sh --only-ok --latex --prefix=redis /data/analytics-data/vmdata/Redis1/Redis.csv /data/analytics-data/vmdata/Redis1 /data/analytics-data/vmdata/Redis2 /data/analytics-data/vmdata/Redis3 /data/analytics-data/vmdata/Redis4 /data/analytics-data/vmdata/Redis5 >latex/redis-nondet.tex

./postprocessing/nondet.sh --only-ok --latex --prefix=memcached /data/analytics-data/vmdata/Memcached2/Memcached.csv /data/analytics-data/vmdata/Memcached1 /data/analytics-data/vmdata/Memcached2 /data/analytics-data/vmdata/Memcached3 /data/analytics-data/vmdata/Memcached4 /data/analytics-data/vmdata/Memcached5 >latex/memcached-nondet.tex

./postprocessing/nondet.sh --only-ok --latex --prefix=git /data/analytics-data/vmdata/Git1/Git.csv /data/analytics-data/vmdata/Git1 /data/analytics-data/vmdata/Git2 /data/analytics-data/vmdata/Git3 /data/analytics-data/vmdata/Git4 /data/analytics-data/vmdata/Git5 >latex/git-nondet.tex
