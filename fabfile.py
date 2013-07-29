from fabric.api import *

# Analytics modules
from _Memcached import *
from _Redis import *
from _Zeromq import *

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
 
    def go(self):
        """ run all the tests for every version specified in a new container """

        # get the list of commits SHA 
        r = self.pclass(self.image, 'root', 'root')
        r.spawn()
        clist = r.get_commit_list(self.commits)
        r.halt()

        # clist is like ['73ae855__antirez__1373553520', '3fc7f32__antirez__1373553467']
        for i in clist:            
            a = i.split('__')
            commit_id = a[0]
            timestamp = a[1]
            author_name = a[2]

            c = self.pclass(self.image, 'root', 'root')
            c.spawn()
            c.checkout(commit_id)
            c.compile()    # long steps
            c.make_test()  #
            c.overall_coverage()
            c.backup(commit_id)
            c.patch_coverage()
            c.collect(author_name, timestamp )
            c.halt()

        

def main():
    """ let's do something """

    # Archetype:
    # X = Analytics(Program, docker image, commits)
    
    # Redis
    r = Analytics(Redis, 'manlio/red-covered', 1)
    r.go()

    # Memcached
    m = Analytics(Memcached, 'manlio/memcached-covered', 1)
    m.go()

    # Zeromq
    z = Analytics(Zeromq, 'manlio/zeromq', 1)
    z.go()


if __name__== "__main__":
    main()
