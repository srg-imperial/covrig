from fabric.api import *

# Analytics modules
from Container import Container


class Beanstalkd(Container):
    """ Beanstalkd class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)
        
        # set variables
        self.path = '/home/beanstalkd'
        self.source_path = '/home/beanstalkd'
        self.tsuite_path = ('/home/beanstalkd/testheap.c', '/home/beanstalkd/testjobs.c',
                            '/home/beanstalkd/testserv.c', '/home/beanstalkd/testutil.c',
                            '/home/beanstalkd/heap-test.c', '/home/beanstalkd/integ-test.c',
                            '/home/beanstalkd/job-test.c', '/home/beanstalkd/util-test.c',
                            '/home/beanstalkd/tests', '/home/beanstalkd/sh-tests',
                            '/home/beanstalkd/ct')
        # set timeout (in seconds) for the test suite to run
        self.timeout = 60

  
    def compile(self):
        """ compile Beanstalkd """
        with cd(self.path):
           with settings(warn_only=True):
               # the developers got rid of autotools starting at fa96ec4
               # thus the first two steps are needed only for older commtis
               run('rm -rf ct && cp -r /home/ct.git/ct .')
               run('./autogen.sh && ./configure')
               run("sed -i 's#tests/cutcheck: tests/cutcheck.o $(objects) $(tests:.c=.o)#tests/cutcheck: tests/cutcheck.o $(objects) $(tests:.c=.o); cc $(CFLAGS) tests/cutcheck.o $(objects) $(tests:.c=.o) -lcut -o tests/cutcheck#' Makefile");
               result = run("make CFLAGS='-O0 --coverage -Wl,--no-as-needed -levent -lrt' LDFLAGS='--coverage -Wl,--no-as-needed -levent -lrt'")
               if result.failed:
                   self.compileError = True

    def make_test(self):
        super(Beanstalkd, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd(self.path):
                with settings(warn_only=True):
                    result = run("make check CFLAGS='-O0 --coverage -Wl,--no-as-needed -levent -lrt' LDFLAGS='--coverage -Wl,--no-as-needed -levent -lrt'")
                    if result.failed:
                        self.maketestError = result.return_code
                    
