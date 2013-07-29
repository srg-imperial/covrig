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
    
    def __init__(self, _pclass, _image, _path, _source_path, _tsuite_path, _commits):
        # the class itself
        self.pclass = _pclass
        # docker image
        self.image = _image
        # path for the program to be built-in in the container image
        self.path = _path
        # source path
        self.source_path = _source_path
        # test suite path
        self.tsuite_path = _tsuite_path
        # commits
        self.commits = _commits
 
    def get_commit_list(self):
        """ get the list of the commits to be analyzed """
        # get the log list; the perl one-liner is to get rid of the damn colored output
        commit_list = run('cd ' + self.source_path + ' && git log -' + 
                          str(self.commits) + " --format=%h__%ct__%an | perl -pe 's/\e\[?.*?[\@-~]//g' ")
        return commit_list.splitlines()

    def go(self):
        """ run all the tests for every version specified in a new container """

        # get the list of commits SHA 
        r = self.pclass(self.image, 'root', 'root')
        r.spawn()
        clist = self.get_commit_list()
        r.halt()

        # clist is like ['73ae855__antirez__1373553520', '3fc7f32__antirez__1373553467']
        for i in clist:            
            a = i.split('__')
            commit_id = a[0]
            timestamp = a[1]
            author_name = a[2]

            # run a new container; remember that c is now an instance of SubClass(Container)!
            c = self.pclass(self.image, 'root', 'root')
            c.spawn()
            c.checkout(self.path, commit_id)
            c.compile()    # long steps
            c.make_test()  #
            c.overall_coverage(self.source_path)
            c.backup(self.path, commit_id)
            c.patch_coverage(self.path)
            c.collect(self.source_path, self.tsuite_path, author_name, timestamp )
            c.halt()

        

def main():
    """ let's do something """

    # Archetype:
    # x = Analytics(Program,
    #               docker image,
    #               absolute path,     
    #               source path,         # where the .gcno files are
    #               (test suite path),   # must be a tuple
    #               commits              # e.g. 10 means "last 10 commits"
    #               )
    
    # Redis
    r = Analytics(Redis, 
                  'manlio/redis', 
                  '/home/redis', 
                  '/home/redis/src', 
                  ('/home/redis/tests',),
                  1,
                  )
    r.go()

    # Memcached
    m = Analytics(Memcached, 
                  'manlio/memcached',  
                  '/home/memcached', 
                  '/home/memcached', 
                  ('/home/memcached/t','/home/memcached/testapp.c'),
                  2,
                  )
    m.go()

    # Zeromq
    z = Analytics(Zeromq,
                  'manlio/zeromq',
                  '/home/zeromq3-x',
                  '/home/zeromq3-x/src',
                  ('/home/zeromq3-x/tests',),
                  2
                  )
    z.go()


if __name__== "__main__":
    main()
