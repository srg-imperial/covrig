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
    def run_custom(cls, _pclass, _image, _commits):
        """ process a custom range of commits, given as tuple """
        r = _pclass(_image, 'root', 'root')
        clist = []
        r.spawn()
        # attach timestamp and author to the commit
        for c in _commits:
            new = r.get_commit_custom(c)
            clist.append(new)
        r.halt()
        return cls(_pclass, _image, clist)
        
    def go(self):
        """ run all the tests for every version specified in a new container """
        # self.commits format is ['commit.id__author.name__timestamp']

        for i in self.commits:            
            a = i.split('__')
            commit_id = a[0]
            timestamp = a[1]
            author_name = a[2]

            c = self.pclass(self.image, 'root', 'root')
            c.spawn()
            c.checkout(commit_id)
            c.tsize_compute()
            c.compile()    # long steps
            c.make_test()  #
            c.prepare_coverage()
            c.overall_coverage()
            c.backup(commit_id)
            c.patch_coverage()
            c.collect(author_name, timestamp )
            c.halt()
            
        

def main():
    """ let's do something """

    g = Analytics.run_custom(Git, 'manlio/git', ('0d8beaa',))
    g.go()

    #l = Analytics.run_custom(Lighttpd, 'manlio/lighttpd', ('eb9f6aa',))
    #l.go()

    #m = Analytics.run_custom(Memcached, 'manlio/memcached', ('57a9856',))
    #m.go()

    #z = Analytics.run_custom(Zeromq, 'manlio/zeromq', ('f5a9c32',))
    #z.go()


    # -> Examples:

    # Test the last N revisions
    # rl = Analytics.run_last(Redis, 'manlio/redis', 3)
    # rl.go()

    # Test a custom set of revisions
    # z = Analytics.run_custom(Memcached, 'manlio/memcached', ('50d7188',))
    # z.go()

    # Use Analyzer() to get the list of all commits with 0 ELOCs
    # z = ZeroCoverage('plot/data/Redis/Redis.csv')
    # z.compute()
    # ...and re-run them:
    # j = Analytics.run_custom(Redis, 'manlio/redis', z.zerocov)
    # j.go()
    


if __name__== "__main__":
    main()
