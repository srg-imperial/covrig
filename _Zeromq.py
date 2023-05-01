from fabric import Connection

# Analytics modules
from Container import Container


class Zeromq(Container):
    """ Zeromq class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/zeromq4-x'").stdout.strip()
        else:
            self.path = '/home/zeromq4-x'
            self.source_path = '/home/zeromq4-x/src'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 120

        self.tsuite_path = ('tests',)
        self.ignore_coverage_from = ('/usr/include/*', )

    def compile(self):
        """ compile Zeromq """
        with self.conn.cd(self.path):
            #check if revision needs a small fix
            result = self.conn.run('git rev-list --first-parent a563d49 ^c28af41 | grep $(git rev-parse HEAD) || git rev-list --first-parent dc9749f ^e1cc2d4 | grep $(git rev-parse HEAD)', warn=True)
            if result.stdout.strip() != "":
                self.conn.run("sed -i '20s/^$/#include <unistd.h>/' tests/test_connect_delay.cpp", warn=True)
            result = self.conn.run(("sh autogen.sh && sh configure --without-documentation "
                          "--with-gcov=yes CFLAGS='-O0 -fprofile-arcs -ftest-coverage' "
                          "CXXFLAGS='-O0 -fprofile-arcs -ftest-coverage' && make -j4 " ), warn=True)
            # breaks on 3 revisions a3ae0d4 to 6b2304a (compileError), fixed in 9a6b875 (test_ctx_options_SOURCES = test_ctx_options.cpp)
            if result.failed:
                self.compileError = True

    def make_test(self):
        super(Zeromq, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if not self.compileError:
            with self.conn.cd(self.path):
                for i in range(5):
                    result = self.conn.run(("ulimit -n 64000 && timeout " + str(self.timeout) +
                                  " make check CFLAGS='-O0' CXXFLAGS='-O0'"), warn=True)
                    if result.failed:
                        self.maketestError = result.return_code
