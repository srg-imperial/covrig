from fabric.api import *

# Analytics modules
from Container import Container


class Lighttpd(Container):
    """ Lighttpd class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if (self.offline):
            self.path = local("realpath 'repos/lighttpd1.4'", capture=True)
        else:
            self.path = '/home/lighttpd1.4'
            self.source_path = '/home/lighttpd1.4/src'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 200

        self.tsuite_path = ('tests', )
        self.ignore_coverage_from = ('/usr/include/*', )


    def compile(self):
        """ compile Lighttpd """
        with cd(self.path):
            with settings(warn_only=True):
                result = run(("./autogen.sh && " +
                              "CFLAGS='--coverage' LDFLAGS='--coverage' " +
                              "LUA_LIBS='-L/usr/lib -llua5.1' LUA_CFLAGS='-I/usr/include/lua5.1' " +
                              "./configure --with-lua --with-openssl --with-zlib --with-bzip2 && " +
                              "make -j`grep -c '^processor' /proc/cpuinfo`"))
                if result.failed:
                    self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Lighttpd, self).make_test()
        # if compile failed, skip this step
        if self.compileError == False:
            with cd(self.path):
                with settings(warn_only=True):
                    result = run('timeout ' + str(self.timeout) + ' make check')
                    if result.failed:
                        self.maketestError = result.return_code
 
