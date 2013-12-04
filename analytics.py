from fabric.api import *
import argparse
import subprocess

# Analytics modules
from _Memcached import *
from _Redis import *
from _Zeromq import *
from _Lighttpd import *
from _Beanstalkd import *
from _Git import *
from _Diffutils import *
from _Binutils import *
from _Findutils import *

# Flow of control:
#  Analytics() set up a cycle of containers using Container() + Subclass(Container)
#  Subclass() runs the tests and store results in a Collector()
#  Collector() is passed to DataHandler(), which dumps data to a CSV output file


""" cleaning functions to clean old/running containers """
def clean_r():
    """ stop all running containers """
    local("docker ps | awk '{print $1}' | xargs docker stop")

def clean_s():
    """ delete all container being run so far """
    local("docker ps -a | grep 'ago' | awk '{print $1}' | xargs docker rm")

def clean_a():
    clean_r()
    clean_s()



class Analytics(object):
    """ Main class """
    
    def __init__(self, _pclass, _image, _commits):
        # the class itself
        self.pclass = _pclass
        # docker image
        self.image = _image
        # commits
        self.commits = _commits
 
    @classmethod
    def run_last(cls, _pclass, _image, _commit):
        """ process the last n commits """
        r = _pclass(_image, 'root', 'root')
        r.spawn()
        clist = r.get_commits(_commit)
        r.halt()
        return cls(_pclass, _image, clist)

    @classmethod
    def run_custom(cls, _pclass, _image, _commit, _count, _startaftercommit=None):
        """ process a custom range of commits, given as tuple """
        r = _pclass(_image, 'root', 'root')
        clist = []
        r.spawn()
        # attach timestamp and author to the commit
        clist = r.get_commits(_count+1, _commit)
        r.halt()

        if _startaftercommit:
          #keep the whole list by default
          startindex = len(clist)
          for index,c in enumerate(clist):
            if c.startswith("%s__" % _startaftercommit):
              startindex = index
              break
          print "Retaining %d revisions" % startindex
          clist = clist[:startindex]
        return cls(_pclass, _image, clist)
        
    def go(self):
        """ run all the tests for every version specified in a new container """

        # list of uncovered files (and corresponding lines) i revisions ago
        prev_uncovered_list = [ ([], []) ] * 10

        # check oldest commit first. this makes it easier to check patch coverage in subsequent versions
        prev_commit_id = self.commits[-1].split('__')[0]
        del self.commits[-1]
        self.commits.reverse()
        for i in self.commits: 
            # self.commits format is ['commit.id__author.name__timestamp']
            print i
            a = i.split('__')
            commit_id = a[0]
            timestamp = a[1]
            author_name = a[2]

            c = self.pclass(self.image, 'root', 'root')
            c.spawn()
            try:
              c.checkout(prev_commit_id, commit_id)
              if not c.emptyCommit:
                c.tsize_compute()
                if not c.offline:
                  c.compile()    # long steps
                  c.make_test()  #
                c.overall_coverage()
                if not c.offline:
                  c.backup(commit_id)
                c.patch_coverage(prev_commit_id)
              for i, (files, lines) in enumerate(prev_uncovered_list):
                prev_uncovered_list[i] = c.prev_patch_coverage(i, files, lines)

              print (c.changed_files, c.uncovered_lines_list)
              prev_uncovered_list.insert(0, (c.changed_files, c.uncovered_lines_list));
              prev_uncovered_list.pop()

              c.collect(author_name, timestamp )
            finally:
              c.halt()
            if c.compileError == False:
              prev_commit_id = commit_id
        

def main():
  parser = argparse.ArgumentParser(prog='Analytics')
  parser.add_argument('--offline', action="store_const", const=True, default=False,
      help="process the revisions reusing previous coverage information")
  parser.add_argument('--resume', action="store_const", const=True, default=False,
      help="resume processing from the last revision found in data file (e.g. /data/<program>/<program>.csv")
  parser.add_argument('program', help="program to analyse")
  parser.add_argument('revisions', type=int, nargs='?', default=0, help="number of revisions to process")
  args = parser.parse_args()

  image = "offline" if args.offline else "baseline"

  benchmarks = {
      "lighttpd" : { "class": Lighttpd, "revision": "0d40b25", "n": 400 },
      "memcached": { "class": Memcached, "revision": "87e2f36", "n": 409 },
      "zeromq"   : { "class": Zeromq, "revision": "573d7b0", "n": 500 },
      "redis"    : { "class": Redis, "revision": "347ab78", "n": 500 },
      "binutils" : { "class": Binutils, "revision": "a0a1bb07", "n": 5000 },
      "diffutils": { "class": Diffutils, "revision": "b2f1e4b", "n": 350 },
      }
  b = benchmarks[args.program]
  if b:
    lastrev = None
    if args.resume:
      output = "data/%s/%s.csv" % (b["class"].__name__, b["class"].__name__)
      lastrecord = subprocess.check_output(["tail", "-1", output])
      lastrecord = lastrecord.split(',')
      if len(lastrecord):
        lastrev = lastrecord[0]
    container = Analytics.run_custom(b["class"], image, b["revision"], args.revisions if args.revisions else b["n"], lastrev)
    container.go()
  else:
    print "Unrecognized program name %s" % args.program

if __name__== "__main__":
    main()