from fabric import Connection

# Analytics modules
from Container import Container


class Apr(Container):
    """ Apr class """

    # Mainly followed instructions from https://github.com/apache/apr/blob/trunk/README to generate coverage data

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.conn.local("realpath 'repos/apr'", capture=True)
        else:
            self.path = '/home/apr'
            self.source_path = '/home/apr'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 200

        self.tsuite_path = ('test',)
        self.ignore_coverage_from = ('include/*',)

    def compile(self):
        """ compile Apr """
        with self.conn.cd(self.path):
            result = self.conn.run('./buildconf && ./configure --with-libxml2 CFLAGS="--coverage" LDFLAGS="--coverage"', warn=True)
            result = self.conn.run('make -j3', warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Apr, self).make_test()
        # if compile failed, skip this step
        if not self.compileError and not self.emptyCommit:
            with self.conn.cd(self.tsuite_path[0]): # we (unusually) cd into the test directory to run the tests
                result = self.conn.run("make", warn=True)
                result = self.conn.run(f"timeout {self.timeout} ./testall", warn=True)
                if result.failed:
                    self.maketestError = result.return_code
