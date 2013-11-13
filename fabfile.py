from fabric.api import *

# Analytics modules
from Analyzer import *
from _Memcached import *
from _Redis import *
from _Zeromq import *
from _Lighttpd import *
from _Beanstalkd import *
from _Git import *

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
    def run_last(cls, _pclass, _image, _commits):
        """ process the last n commits """
        r = _pclass(_image, 'root', 'root')
        r.spawn()
        clist = r.get_commit_list(_commits)
        r.halt()
        return cls(_pclass, _image, clist)

    @classmethod
    def run_custom(cls, _pclass, _image, _commits, _count):
        """ process a custom range of commits, given as tuple """
        r = _pclass(_image, 'root', 'root')
        clist = []
        r.spawn()
        # attach timestamp and author to the commit
        for c in _commits:
            new = r.get_commit_custom(c, _count+1)
            clist += new
        r.halt()
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
            a = i.split('__')
            commit_id = a[0]
            timestamp = a[1]
            author_name = a[2]

            c = self.pclass(self.image, 'root', 'root')
            c.spawn()
            try:
              c.checkout(commit_id)
              c.tsize_compute()
              c.compile()    # long steps
              c.make_test()  #
              c.overall_coverage()
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
    # exact revisions for reproducibility across containers
    l = Analytics.run_custom(Lighttpd, 'baseline', ('0d40b25',), 275)
    l.go()

    m = Analytics.run_custom(Memcached, 'baseline', ('87e2f36',), 289)
    m.go()
    
    z = Analytics.run_custom(Zeromq, 'baseline', ('573d7b0',), 1100)
    z.go()

    rl = Analytics.run_custom(Redis, 'baseline', ('347ab78',), 1200)
    rl.go()

    #rl = Analytics.run_custom(Beanstalkd, 'beanstalkd', ('157d88bf9435a23b71a1940a9afb617e52a2b9e9',), 600)
    #rl = Analytics.run_custom(Git, 'git', ('aa2706463f',), 50)
    
    #rl.go()

    # Use Analyzer() to get the list of all commits with 0 ELOCs
    # z = ZeroCoverage('plot/data/Redis/Redis.csv')
    # z.compute()
    # ...and re-run them:
    # j = Analytics.run_custom(Redis, 'manlio/redis', z.zerocov)
    # j.go()
    


if __name__== "__main__":
    main()
