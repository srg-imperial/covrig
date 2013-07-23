from fabric.api import *

# Analytics modules
from XMLHandler import *

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
            run('git checkout ' + revision)

    def overall_coverage(self, path):
        """ collect overall coverage results """
        if self.compileError == False and self.maketestError != 1:
            with cd(path):
                run('gcov * | tail -1 > coverage-' + self.current_revision) 

    def collect(self, source_path, tsuite_path):
        """ create a Collector to collect all info and a XMLHandler to parse them """
        c = Collector()
        # the class name which is actually running this method, as a string
        c.name = self.__class__.__name__
        c.revision = self.current_revision
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
            c.summary = run('cat ' + source_path + '/coverage-' + self.current_revision)
            c.compileError = self.compileError
            c.maketestError = self.maketestError

        # pass the Collector() obj to the XML handler to store results in nice XML
        x = XMLHandler(c)
        x.extractData()
        x.dumpXML()



class Redis(Container):
    """ redis class """
    
    def __init__(self, _image, _user, _pwd, _current_revision):
        Container.__init__(self, _image, _user, _pwd)
        # revision we're working with
        self.current_revision = _current_revision

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

    def __init__(self, _image, _user, _pwd, _current_revision):
        Container.__init__(self, _image, _user, _pwd)
        # revision we're working with
        self.current_revision = _current_revision

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

    def __init__(self, _image, _user, _pwd, _current_revision):
        Container.__init__(self, _image, _user, _pwd)
        # revision we're working with
        self.current_revision = _current_revision

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
    
    def __init__(self, _pclass, _image, _path, _source_path, _tsuite_path, _revisions):
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
        # revisions #
        self.revisions = _revisions
 
    def get_tags(self):
        """ get the list of all tagged revisions """
        self.taglist = local('cd ' + self.localrepo + 
                             ' && git tag | sort --version-sort', capture=True)

    def go(self):
        """ run all the tests for every version specified in a new container """
        for i in self.revisions:
            print i
            r = self.pclass(self.image, 'root', 'root', i)
            r.spawn()
            r.checkout(self.path, i)
            r.compile()    # long steps
            r.make_test()  #
            r.overall_coverage(self.source_path)
            r.collect(self.source_path, self.tsuite_path)
            r.halt()
        

def main():
    """ let's do something """

    # Archetype:
    #x = Analytics(Program,
    #              docker image,
    #              absolute path,     
    #              source path,         # where the .gcno files are
    #              (test suite path),   # must be a tuple
    #              (versions)
    #              )
    
    # Redis
    r = Analytics(Redis, 
                  'manlio/redis', 
                  '/home/redis', 
                  '/home/redis/src', 
                  ('/home/redis/tests',),
                  ('2.6.14','2.6.13')
                  )
    r.go()

    # Memcached
    m = Analytics(Memcached, 
                  'manlio/memcached',  
                  '/home/memcached', 
                  '/home/memcached', 
                  ('/home/memcached/t','/home/memcached/testapp.c'),
                  ('1.4.15','1.4.14')
                  )
    m.go()

    # Zeromq
    z = Analytics(Zeromq,
                  'manlio/zeromq',
                  '/home/zeromq3-x',
                  '/home/zeromq3-x/src',
                  ('/home/zeromq3-x/tests',),
                  ('v3.2.3',)
                  )
    z.go()


if __name__== "__main__":
    main()
