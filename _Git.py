from fabric import Connection

# Analytics modules
from Container import Container


class Git(Container):
    """ Git class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/git'").stdout.strip()
        else:
            self.path = '/home/git'
            self.source_path = '/home/git'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 7200

        self.tsuite_path = ('t', 'test-*')
        self.ignore_coverage_from = ('/usr/include/*', )

    def compile(self):
        """ compile Git """
        with self.conn.cd(self.path):
            # for later versions, need -std=c99
            # make configure && ./configure && make -j`grep -c '^processor' /proc/cpuinfo` coverage-compile
            result = self.conn.run("make configure && ./configure CFLAGS='-std=c99' && make -j`grep -c '^processor' /proc/cpuinfo` coverage-compile", warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Git, self).make_test()
        # if compile failed, skip this step
        if not self.compileError:
            with self.conn.cd(self.path):
                result = self.conn.run("timeout " + str(self.timeout) + " make coverage", warn=True)
                if result.failed:
                    self.maketestError = result.return_code
