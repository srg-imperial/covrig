from fabric.api import *

# Analytics modules
from Container import Container


class Zeromq(Container):
    """ Zeromq class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if (self.offline):
          self.path = local("realpath 'repos/zeromq4-x'", capture=True)
        else:
          self.path = '/home/zeromq4-x'
          self.source_path = '/home/zeromq4-x/src'
          # set timeout (in seconds) for the test suite to run
          self.timeout = 120

        self.tsuite_path = ('tests',)
        self.ignore_coverage_from = ('/usr/include/*', )

    def compile(self):
        """ compile Zeromq """
        with cd(self.path):
           with settings(warn_only=True):
               #check if revision needs a small fix
               result = run('git rev-list --first-parent a563d49 ^c28af41 | grep $(git rev-parse HEAD) || git rev-list --first-parent dc9749f ^e1cc2d4 | grep $(git rev-parse HEAD)')
               if result.succeeded:
                 run("sed -i '20s/^$/#include <unistd.h>/' tests/test_connect_delay.cpp")
               result = run(("sh autogen.sh && sh configure --without-documentation "
                             "--with-gcov=yes CFLAGS='-O0 -fprofile-arcs -ftest-coverage' "
                             "CXXFLAGS='-O0 -fprofile-arcs -ftest-coverage' && make -j4 " ))
               if result.failed:
                   self.compileError = True

    def make_test(self):
        super(Zeromq, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd(self.path):
                with settings(warn_only=True):
                  for i in range(5):
                    result = run(("timeout " + str(self.timeout) + 
                                  " make check CFLAGS='-O0' CXXFLAGS='-O0'"))
                    if result.failed:
                        self.maketestError = result.return_code
