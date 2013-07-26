from fabric.api import *

# Analytics modules
from DataHandler import *

# Flow of control:
#  Analytics() set up a cycle of containers using Container() + Subclass(Container)
#  Subclass() runs the tests and store results in a Collector()
#  Collector() is passed to XMLHandler(), which dumps data to XML


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



class Container(object):
    """ Class used to spawn a new container with sshd listening """

    def __init__(self, _image, _user, _pwd):
        self.image = _image
        self.user = _user
        self.pwd = _pwd
        # no errors yet :)
        self.compileError = False
        self.maketestError = False

    # The following are methods used to spawn a new container
    #

    def sshd_up(self):
        """ set up sshd """
        self.cnt_id = local('docker run -d -p 22 ' + self.image + 
                            ' /usr/sbin/sshd -D', capture=True)
        
    def set_ip(self):
        """ set container ID """
        self.ip = local("docker inspect " + self.cnt_id + 
                        " | grep IPAddress | awk '{print $2}'", capture=True)
        self.ip = self.ip.strip(',"')

    def fabric_setup(self):
        """ set fabric env parameters """
        env.user = self.user
        env.password = self.pwd
        env.host_string = self.ip

    def run_test(self):
        """ uname to check everything works """
        run('uname -on')

    def spawn(self):
        """ call all the methods needed to spawn a container """
        self.sshd_up()
        self.set_ip()
        self.fabric_setup()

    def halt(self):
        """ shutdown the current container """
        print '\n\nHalting the current container...\n\n'
        local('docker stop ' + self.cnt_id)

    # The following are methods used to perform actions common to several containers
    #

    def count_sloc(self, path):
        """ use cloc to get the static lines of code for any given file or directory """
        lines = 0
        for p in path:
            lines += int(run("cloc " + p + " | tail -2 | awk '{print $5}'"))
        return str(lines)
            
    def checkout(self, path, revision):
        """ checkout the revision we want """
        with cd(path):
            # set the revision for current execution (commit sha)
            self.current_revision = revision
            # checkout revision
            run('git checkout ' + revision)

    def backup(self, path, commit):
        """ create a tar.gz with all the .gcda and .gcno files and save it to localhost """
        with cd(path):
            cnid = 'coverage-' + commit
            run('mkdir ' + cnid)
            # find all the gcno/gcda files and copy them to ~/coverage-xxxxx/
            run("find . -iname *.gcno | xargs -I '{}' cp {} " + cnid)
            run("find . -iname *.gcda | xargs -I '{}' cp {} " + cnid)
            # save gcov/gcc/g++ info
            with cd(cnid):
                run('gcov -v | head -1 > build_info.txt')
                run('echo >> build_info.txt')
                run('gcc -v &>> build_info.txt')
                # don't raise any error if g++ is not installed 
                with settings(warn_only=True):
                    run('echo >> build_info.txt')
                    run('g++ -v &>> build_info.txt')
            # create an archive
            run('tar -cjf ' + cnid + 'tar.bz2 ' + cnid)
            # scp to localhost (get <remote path> , <local path>)
            local('mkdir -p data/' + self.__class__.__name__)
            get(cnid + 'tar.bz2', 'data/' + self.__class__.__name__ + '/' + cnid + '.tar.bz2')
            
    def overall_coverage(self, path):
        """ collect overall coverage results """
        if self.compileError == False and self.maketestError != 1:
            with cd(path):
                run('gcov * | tail -1 > coverage.txt') 

    def collect(self, source_path, tsuite_path, author_name, timestamp):
        """ create a Collector to collect all info and a XMLHandler to parse them """
        c = Collector()
        # the class name which is actually running this method, as a string
        c.name = self.__class__.__name__
        # fill in some info about the test
        c.revision = self.current_revision
        c.author_name = author_name
        c.timestamp = timestamp
        # compute test suite size as SLOC. Note tsuite_path MUST be a tuple!
        c.tsuite_size = self.count_sloc(tsuite_path)
        # if compilation failed
        if self.compileError == True:
            c.compileError = True
        # if the test suite failed (i.e. the test suite is broken or cannot be run)
        elif self.maketestError == 1:
            c.maketestError = True
        # proceed in all other cases
        else:
            c.summary = run('cat ' + source_path + '/coverage.txt')
            c.compileError = self.compileError
            c.maketestError = self.maketestError

        # pass the Collector() obj to the XML handler to store results in nice XML
        x = XMLHandler(c)
        x.extractData()
        x.dumpCSV()



class Redis(Container):
    """ redis class """
    
    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

    def compile(self):
        """ compile redis """
        with cd('/home/redis'):
           with settings(warn_only=True):
               result = run('make clean && make gcov')
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd('/home/redis/src'):
                with settings(warn_only=True):
                    result = run('make test')
                    if result.failed:
                        self.maketestError = result.return_code
                


class Memcached(Container):
    """ Memcached class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)
  
    def compile(self):
        """ compile Memcached """
        with cd('/home/memcached'):
           with settings(warn_only=True):
               result = run(("sh autogen.sh && sh configure && make clean && "
                             "make CFLAGS+='-fprofile-arcs -ftest-coverage -g -O0 -pthread'"))
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd('/home/memcached'):
                with settings(warn_only=True):
                    result = run('make test')
                    if result.failed:
                        self.maketestError = result.return_code



class Zeromq(Container):
    """ Zeromq class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

    def compile(self):
        """ compile Zeromq """
        with cd('/home/zeromq3-x'):
           with settings(warn_only=True):
               result = run(("sh autogen.sh && sh configure --without-documentation "
                             "--with-gcov=yes CFLAGS='-O0 -fprofile-arcs -ftest-coverage' "
                             "CXXFLAGS='-O0 -fprofile-arcs -ftest-coverage' && make -j4 " ))
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd('/home/zeromq3-x'):
                with settings(warn_only=True):
                    result = run(("make check CFLAGS='-O0' CXXFLAGS='-O0'"))
                    if result.failed:
                        self.maketestError = result.return_code
            # extra coverage steps
            with cd('/home/zeromq3-x/src'):
                # moving the gcov files to the right place
                run('mv .libs/*.gcda .')
                run('mv .libs/*.gcno .')
                # remove 'libzmq_la-' prefix from gcov files
                run("rename 's/libzmq_la-//' *.gcda")
                run("rename 's/libzmq_la-//' *.gcno")



class Analytics(object):
    """ Main class. Usage: Analytics(custom program class, docker_image, revisions (tuple)) """
    
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
            c.backup(self.path, commit_id)
            c.overall_coverage(self.source_path)
            c.collect(self.source_path, self.tsuite_path, author_name, timestamp )

        

def main():
    """ let's do something """

    # Archetype:
    #x = Analytics(Program,
    #              docker image,
    #              absolute path,     
    #              source path,         # where the .gcno files are
    #              (test suite path),   # must be a tuple
    #              commits              # e.g. 10 means "last 10 commits"
    #              )
    
    # Redis
    r = Analytics(Redis, 
                  'manlio/redis', 
                  '/home/redis', 
                  '/home/redis/src', 
                  ('/home/redis/tests',),
                  5,
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
                  5
                  )
    z.go()


if __name__== "__main__":
    main()
