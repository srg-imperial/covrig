Analytics
=========

Usage
-----

```
python analytics.py <benchmark>
```

benchmark is one lighttpd, redis, memcached, zeromq, binutils

The full options are

```
usage: python analytics.py [-h] [--offline] [--resume] [--limit LIMIT] [--output OUTPUT]
                           program [revisions]

positional arguments:
  program          program to analyse
  revisions        number of revisions to process

optional arguments:
  -h, --help       show this help message and exit
  --offline        process the revisions reusing previous coverage information
  --resume         resume processing from the last revision found in data file
                   (e.g. data/<program>/<program>.csv)
  --limit LIMIT    limit to n number of revisions
  --output OUTPUT  output file name
```

---

Scenario: `python analytics.py redis` was interrupted (bug in the code, power failure, etc.)

Solution: `python analytics.py --resume redis`. For accurate latent patch coverage info, also run `python analytics.py --offline redis`

---

Scenario: `python analytics.py zeromq 300` executed correctly but you realised that you need to analyse 500 revisions

Solution: `python analytics.py --limit 200 zeromq 500` analyses the previous 200 revisions and appends them to the csv output. `postprocessing/regen.sh data/Zeromq/Zeromq.csv repos/zeromq/` will regenerate the output file, putting all the lines in order (you need repos/zeromq to be a valid zeromq git repostory). For accurate latent patch coverage info, also run `python analytics.py --offline zeromq 500`

---

Scenario: Experiments were executed. How to get meaningful data?

Solution: Run `postprocessing/makeartefacts.sh`. Graphs are placed in graphs/, LaTeX defines are placed in latex/

---

Scenario: How to get non-determinism data?

Solution: Run the same benchmark multiple times
```
for I in 1 2 3 4 5; do python analytics.py --output Redis$I redis ; done
```

To get the results, run
```
postprocessing/nondet.sh data/Redis1/Redis.csv data/Redis1 data/Redis2 data/Redis3 data/Redis4 data/Redis5
```
