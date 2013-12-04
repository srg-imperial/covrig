from fabric.api import *

# Analytics modules
from Container import Container


class Binutils(Container):
    """ Binutils class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if (self.offline):
          self.path = local("realpath 'repos/binutils'", capture=True)
        else:
          self.path = '/home/binutils'
          self.source_path = '/home/binutils/binutils'
          # set timeout (in seconds) for the test suite to run
          self.timeout = 60

        self.tsuite_path = ('binutils/testsuite', )
        self.limit_changes_to = ('binutils', )
        self.ignore_coverage_from = ('include/*' ,)

    def compile(self):
        """ compile Binutils """
        with cd(self.path):
           with settings(warn_only=True):
               result = run('./configure && ' + 
                   ' make -j2 CFLAGS=\"-O0 -coverage -Wno-error\" LDFLAGS=\"-coverage\"')
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Binutils, self).make_test()
        # if compile failed, skip this step
        if not self.compileError and not self.emptyCommit: 
            with settings(warn_only=True):
              with cd(self.source_path):
                    result = run(("timeout " + str(self.timeout) + 
                                  " make check CFLAGS=\"-coverage -O0\" LDFLAGS=\"-coverage\""))
                    if result.failed:
                        self.maketestError = result.return_code