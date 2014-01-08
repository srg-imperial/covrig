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

---

Scenario: I have a list of revisions. How do I get more interesting information about them?

Solution:  Run
```
./postprocessing/fixcoverage-multiple.sh repos/memcached/ bugs/bugs-memcached.simple data/Memcached/ data/Memcached/Memcached.csv
```
The first argument is a local clone of the target git repository, the second argument is a file with the list of revisions which fix bugs (one per line), the third argument is a folder which contains the results of the analytics.py script and the optional fourth argument is the analytics .csv output.
The output looks like
```
Looked at 46 fixes (1 unhandled): 179 lines covered, 68 lines not covered
4 fixes did not change/add code, 28 fixes were fully covered
only tests/only code/tests and code 0/18/23
```
This can be used to get details about new tests/code. For example, running this on a list of bug fixing revisions can show how well fixes are tested and whether a regression test is added along with the revision. Running this on a list of bug introducing revisions may show low coverage.

---

Scenario: I have a list of revisions. How do I get more interesting information about the code from the previous revision?

Solution: As before, but use the `postprocessing/faultcoverage-multiple.sh` script.

This can be used to analyse buggy code coverage. Running this on a list of bug fixing revisions is intuitively similar to running the previous script on a list of revisions introducing the respective bugs.
