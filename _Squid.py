from fabric.api import *

# Analytics modules
from Container import Container


class Squid(Container):
    """ squid class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if (self.offline):
            self.path = local("realpath 'repos/squid'", capture=True)
        else:
            self.path = '/home/squid'
            self.source_path = '/home/squid/src'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 90

        self.tsuite_path = ('test-suite',)


    def compile(self):
        """ compile Squid """
        with cd(self.path):
            with settings(warn_only=True):
                result = run("sh bootstrap.sh && " +
                             "sh configure CFLAGS='--coverage' CXXFLAGS='--coverage' LDFLAGS='--coverage' && " +
                             "make -j`grep -c '^processor' /proc/cpuinfo`")
                if result.failed:
                    self.compileError = True


    def make_test(self):
        """ run the test suite """
        super(Squid, self).make_test()
        # if compile failed, skip this step
        if self.compileError == False:
            with cd(self.path):
                with settings(warn_only=True):
                    for i in range(5):
                        result = run('timeout ' + str(self.timeout) + ' make check')
                        if result.failed:
                            self.maketestError = result.return_code
