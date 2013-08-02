from fabric.api import *

# Analytics modules
from Container import Container


class Zeromq(Container):
    """ Zeromq class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        self.path = '/home/zeromq3-x'
        self.source_path = '/home/zeromq3-x/src'
        self.tsuite_path = ('/home/zeromq3-x/tests',)
        # set timeout (in seconds) for the test suite to run
        self.timeout = 120

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
                    result = run(("timeout " + str(self.timeout) + 
                                  " make check CFLAGS='-O0' CXXFLAGS='-O0'"))
                    if result.failed:
                        self.maketestError = result.return_code
            # extra coverage steps
            with settings(warn_only=True):            
                with cd('/home/zeromq3-x/src'):
                    # moving the gcov files to the right place
                    run('mv .libs/*.gcda .')
                    run('mv .libs/*.gcno .')
                    # remove 'libzmq_la-' prefix from gcov files
                    run("rename 's/libzmq_la-//' *.gcda")
                    run("rename 's/libzmq_la-//' *.gcno")
