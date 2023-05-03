from fabric import Connection
import argparse
import subprocess

# Analytics modules
from _Apr import *
from _Curl import *
from _Memcached import *
from _Redis import *
from _Zeromq import *
# from _Lighttpd import *
from _Lighttpd2 import *
# from _Beanstalkd import *
from _Git import *
# from _Diffutils import *
from _Binutils import *
from _BinutilsGdb import *
# from _Findutils import *
from _Dovecot import *
# from _Squid import *
from _Vim import *

# Flow of control:
#  Analytics() set up a cycle of containers using Container() + Subclass(Container)
#  Subclass() runs the tests and store results in a Collector()
#  Collector() is passed to DataHandler(), which dumps data to a CSV output file


""" cleaning functions to clean old/running containers """


def clean_r(c):
    """ stop all running containers """
    # TODO: is this the right way of invoking Connection?
    c.local("docker ps | awk '{print $1}' | xargs docker stop")


def clean_s(c):
    """ delete all container being run so far """
    c.local("docker ps -a | grep 'ago' | awk '{print $1}' | xargs docker rm")


def clean_a():
    # TODO: initialize Connection correctly.
    c = Connection()
    clean_r(c)
    clean_s(c)


class Analytics(object):
    """ Main class """

    def __init__(self, _pclass, _image, _commits):
        # the class itself
        self.pclass = _pclass
        # docker image
        self.image = _image
        # commits
        self.commits = _commits
        # Dummy local connection
        self.conn = Connection('host')

    @classmethod
    def run_last(cls, _pclass, _image, _commit):
        """ process the last n commits """
        r = _pclass(_image, 'root', 'root')
        r.spawn()
        clist = r.get_commits(_commit)
        r.halt()
        return cls(_pclass, _image, clist)

    @classmethod
    def run_custom(cls, _pclass, _image, _commit, _count, _startaftercommit=None, _maxcommits=0):
        """ process a custom range of commits, given as tuple """
        r = _pclass(_image, 'root', 'root')
        clist = []
        r.spawn()
        # attach timestamp and author to the commit
        clist = r.get_commits(_count + 1, _commit)
        r.halt()

        if _startaftercommit:
            # keep the whole list by default
            startindex = len(clist)
            for index, c in enumerate(clist):
                if c.startswith("%s__" % _startaftercommit):
                    startindex = index
                    break
            print("Retaining %d revisions" % startindex)
            clist = clist[:startindex + 1]
        if _maxcommits:
            clist = clist[-(_maxcommits + 1):]
        print("Will analyse %d commits" % len(clist))
        return cls(_pclass, _image, clist)

    def go(self, outputfolder, outputfile):
        """ run all the tests for every version specified in a new container """

        # create a data/program-name directory where data will be collected
        self.conn.local('mkdir -p data/' + outputfolder)
        # list of uncovered files (and corresponding lines) i revisions ago
        prev_uncovered_list = [([], [])] * 10

        # check oldest commit first. this makes it easier to check patch coverage in subsequent versions
        prev_commit_id = self.commits[-1].split('__')[0]
        del self.commits[-1]
        self.commits.reverse()
        for i in self.commits:
            # self.commits format is ['commit.id__author.name__timestamp']
            print(i)
            a = i.split('__')
            commit_id = a[0]
            timestamp = a[1]
            author_name = a[2]

            c = self.pclass(self.image, 'root', 'root')
            c.outputfolder = outputfolder
            c.spawn()
            if c.offline:  # TODO: Don't really know why being offline changes the commit hash length we get...
                prev_commit_id = prev_commit_id[:7]
                commit_id = commit_id[:7]

            try:
                c.checkout(prev_commit_id, commit_id)
                if not c.emptyCommit:
                    c.tsize_compute()
                    if not c.offline:
                        c.compile()  # long steps
                        c.make_test()  #
                    c.overall_coverage()
                    if not c.offline:
                        c.backup(commit_id)
                    c.patch_coverage(prev_commit_id)
                for j, (files, lines) in enumerate(prev_uncovered_list):
                    prev_uncovered_list[j] = c.prev_patch_coverage(j, files, lines)

                print(c.changed_files, c.uncovered_lines_list)
                prev_uncovered_list.insert(0, (c.changed_files, c.uncovered_lines_list))
                prev_uncovered_list.pop()

                c.collect(author_name, timestamp, outputfolder, outputfile)
            finally:
                c.halt()
            if not c.compileError:
                prev_commit_id = commit_id


def main():
    parser = argparse.ArgumentParser(prog='Analytics')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--image', default='baseline',
                       help="specify docker image (default: %(default)s)")
    group.add_argument('--offline', action="store_true",
                       help="process the revisions reusing previous coverage information")
    parser.add_argument('--resume', action="store_true",
                        help="resume processing from the last revision found in data file (e.g. data/<program>/<program>.csv)")
    parser.add_argument('--endatcommit', help="process revisions up to this commit")
    parser.add_argument('--limit', type=int, help="limit to n number of revisions")
    parser.add_argument('--output', help="output file name")
    parser.add_argument('program', help="program to analyse")
    parser.add_argument('revisions', type=int, nargs='?', default=0, help="number of revisions to process")
    args = parser.parse_args()

    benchmarks = {
        "apr": {"class": Apr, "revision": "d54e362", "n": 500},
        "curl": {"class": Curl, "revision": "b3e55bf", "n": 500},
        # "beanstalkd": {"class": Beanstalkd, "revision": "fb0a466", "n": 600},
        # "lighttpd": {"class": Lighttpd, "revision": "c8fbc16", "n": 600},
        "lighttpd2": {"class": Lighttpd2, "revision": "0d40b25", "n": 400},
        "memcached": {"class": Memcached, "revision": "87e2f36", "n": 409},
        "zeromq": {"class": Zeromq, "revision": "573d7b0", "n": 500},
        "redis": {"class": Redis, "revision": "347ab78", "n": 500},
        "binutils": {"class": Binutils, "revision": "a0a1bb07", "n": 6000},
        # In reality only ~2500 commits are relevant (inside binutils/) but binutils-gdb contains many other projects
        "binutils-gdb": {"class": BinutilsGdb, "revision": "26be601", "n": 36106},
        # "diffutils": {"class": Diffutils, "revision": "b2f1e4b", "n": 350},
        # "dovecot": {"class": Dovecot, "revision": "fbf5813", "n": 1000},
        # matches up with mercurial/git-hg commits for ffbf5813, some commits don't work since have external dependencies we can't roll back to (Unicode)
        "dovecot": {"class": Dovecot, "revision": "121b017", "n": 1000},
        # "squid": {"class": Squid, "revision": "fa4c8a3", "n": 1000},
        "git": {"class": Git, "revision": "d7aced9", "n": 500},
        # For Vim, Jun 2013 revision, v7 last rev is edeb846c
        "vim": {"class": Vim, "revision": "f751255", "n": 500},
    }
    try:
        b = benchmarks[args.program]
        outputfolder = args.output if args.output else b["class"].__name__
        outputfile = b["class"].__name__
        if args.offline:
            outputfile += "Offline"
            print('running offline, requires previous coverage information (data/<program>/coverage-<revision>.tar.bz2)')

        output = "data/%s/%s.csv" % (outputfolder, outputfile)
        lastrev = None
        if args.resume:
            lastrecord = subprocess.check_output(["tail", "-1", output])
            lastrecord = lastrecord.decode().split(',')
            if len(lastrecord):
                lastrev = lastrecord[0]
        container = Analytics.run_custom(b["class"],
                                         args.image if not args.offline else None,
                                         args.endatcommit if args.endatcommit else b["revision"],
                                         args.revisions if args.revisions else b["n"], lastrev,
                                         args.limit)
        container.go(outputfolder, outputfile)
    except KeyError:
        print("Unrecognized program name %s" % args.program)


if __name__ == "__main__":
    main()
