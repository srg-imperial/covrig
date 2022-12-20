from fabric.api import *

# Analytics modules
from Container import Container


class Diffutils(Container):
    """ Diffutils class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        self.path = '/home/diffutils'
        self.source_path = '/home/diffutils/src'
        self.tsuite_path = ('/home/diffutils/tests', )
        # set timeout (in seconds) for the test suite to run
        self.timeout = 60

    def compile(self):
        """ compile Diffutils """
        with cd(self.path):
            with settings(warn_only=True):
                run("sed -i 's/\(^perl[ \\t]*\).*$/\\1-/' bootstrap.conf")
                run("sed -i 's@git://git.sv.gnu.org/gnulib.git@/home/gnulib@' .git/config")
                run("sed -i 's@git://git.sv.gnu.org/gnulib.git@/home/gnulib@' .gitmodules")

                result = run('./bootstrap --gnulib-srcdir=/home/gnulib && ./configure && ' +
                             ' make CFLAGS=\"-O0 -coverage\" LDFLAGS=\"-coverage\"')
                if result.failed:
                    self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Diffutils, self).make_test()
        # if compile failed, skip this step
        if self.compileError == False:
            with settings(warn_only=True):
                with cd(self.path):
                    result = run(("timeout " + str(self.timeout) +
                                  " make check CFLAGS=\"-coverage -O0\" LDFLAGS=\"-coverage\""))
                    if result.failed:
                        self.maketestError = result.return_code
