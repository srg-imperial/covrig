from fabric.api import *

# Analycis modules
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
        print '\n===> YEEH if you read this it means everything went alright!'
        print 'Halting the current container...\n\n'
        local('docker stop ' + self.cnt_id)

    def count_sloc(self, path):
        """ use cloc to get the static lines of code for any given directory """
        with cd(path):
            lines = run("cloc . | grep SUM: | awk '{print $5}'")
        return lines



class Redis(Container):
    """ redis class """
    
    def __init__(self, _image, _user, _pwd, _current_revision):
        Container.__init__(self, _image, _user, _pwd)
        # revision we're working with
        self.current_revision = _current_revision
        # no errors yet (:
        self.compileError = False
        self.maketestError = False

    def checkout(self):
        """ checkout the revision we want """
        with cd('/home/redis'):
            run('git checkout ' + self.current_revision)

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
                        self.maketestError = True
        else:
            pass
            
    def overall_coverage(self):
        """ collect overall coverage results """
        if self.compileError == False and self.maketestError == False:
            with cd('/home/redis/src'):
                run('gcov *.c | tail -1 > coverage-' + self.current_revision) 
        else:
            pass
        
    def collect(self):
        """ create a Collector to collect all info and a XMLHandler to parse them """
        # TODO: (?) get rid of the hardcoded bit and move this to Container()
        c = Collector()
        c.revision = self.current_revision
        # if no errors have been detected
        if self.compileError == False and self.maketestError == False:
            c.summary = run('cat /home/redis/src/coverage-' + self.current_revision)
            c.tsuite_size = self.count_sloc('/home/redis/tests/')
        else:
            c.compileError = self.compileError
            c.maketestError = self.maketestError
        # pass the Collector() obj to the XML handler to store results in nice XML
        x = XMLHandler(c)
        x.extractData()
        x.dumpXML()



class Analytics(object):
    """ Main class. Usage: Analytics(custom program class, docker_image, revisions (tuple)) """
    
    def __init__(self, _pclass, _image, _revisions):
        # the class itself
        self.pclass = _pclass
        # the class name as a string
        self.pname = str(_pclass)
        # docker image
        self.image = _image
        self.revisions = _revisions
        # e.g. if program is 'Redis', local dir will be 'Redis-local'
        self.localrepo = self.pname + '-local'        

        # supported project repos
        self.repos = {'Redis' : 'https://github.com/antirez/redis.git'}

    # local_clone() and get_tags() are only useful if the list of versions
    # to be tested is NOT specified as an argument when creating a new 
    # Analytics() object.
    def local_clone(self):
        """ get a local clone to inspect """
        local('mkdir -p analytics && cd analytics')    
        local('git clone ' + self.repos[self.pname] + ' ' + self.localrepo)

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
            r.checkout()
            r.compile()    # long steps
            r.make_test()  #
            r.overall_coverage()
            r.collect()
            r.halt()
        

def main():
    """ let's do something """

    # start a new test targeting Redis, using docker image 'manlio/redis' 
    # and testing revisions 2.4.0, 2.6.14 and 2.6.2

    a = Analytics(Redis, 'manlio/redis', ('2.4.0', '2.6.14', '2.6.2'))
    #a = Analytics(Redis, 'manlio/redis', ('2.4.0',)) # compile error
    a.go()
    
    # Tests:

    # ==> Spawn a new redis container
    # r = Redis('manlio/red-covered', 'root', 'root', '2.6.14')
    # r.spawn()
    # r.overall_coverage()
    # r.collect()
    # r.halt()
    
    # ==> Spawn a new container
    # c = Container('manlio/dev', 'root', 'root')
    # c.spawn()
    # c.halt()


if __name__== "__main__":
    main()
