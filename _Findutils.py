from fabric.api import *

# Analytics modules
from Container import Container


class Findutils(Container):
    """ Findutils class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if (self.offline):
            self.path = local("realpath 'repos/binutils'", capture=True)
        else:
            self.path = '/home/findutils'
            self.source_path = '/home/findutils'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 120

        self.tsuite_path = ('t', 'test-*')
        self.ignore_for_coverage = ('/home/findutils/gl')

    def compile(self):
        """ compile Findutils """
        with cd(self.path):
            with settings(warn_only=True):
                #aufs is broken when it comes to very long paths. disable getcwd path-maxtest

                #still not quite working
                result = run(
                    "./import-gnulib.sh -d /home/gnulib && " +
                    "sed -i 's/while (1)$/while (0)/' gl/m4/getcwd-path-max.m4 && "
                    "aclocal -I m4 -I gl/m4 >/dev/null 2>&1 && " +
                    "autoconf >/dev/null 2>&1 &&" +
                    "./configure ")
                if result.failed:
                    self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Findutils, self).make_test()
        # if compile failed, skip this step
        if self.compileError == False:
            with settings(warn_only=True):
                with cd(self.path + "/find"):
                    result = run(("timeout " + str(self.timeout) +
                                  " make check CFLAGS=\"-coverage -O0\" LDFLAGS=\"-coverage\""))
                with cd(self.path + "/locate"):
                    result = run(("timeout " + str(self.timeout) +
                                  " make check CFLAGS=\"-coverage -O0\" LDFLAGS=\"-coverage\""))
                with cd(self.path + "/xargs"):
                    result = run(("timeout " + str(self.timeout) +
                                  " make check CFLAGS=\"-coverage -O0\" LDFLAGS=\"-coverage\""))
                    if result.failed:
                        self.maketestError = result.return_code
