from fabric import Connection

# Analytics modules
from Container import Container


class Apr(Container):
    """ Apr class """

    # Mainly followed instructions from https://github.com/apache/apr/blob/trunk/README to generate coverage data

    def __init__(self, _image, _user, _pwd, _repeats):
        Container.__init__(self, _image, _user, _pwd, _repeats)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/apr'").stdout.strip()
        else:
            self.path = '/home/apr'
            self.source_path = '/home/apr'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 200

        self.tsuite_path = ('test',)
        self.ignore_coverage_from = ('include/*', '*/test/*')

    def compile(self):
        """ compile Apr """
        with self.conn.cd(self.path):
            result = self.conn.run('./buildconf && CFLAGS="--coverage -fprofile-abs-path" LDFLAGS="--coverage" ./configure --with-libxml2', warn=True)
            result = self.conn.run('make -j3', warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Apr, self).make_test()
        # if compile failed, skip this step
        if not self.compileError and not self.emptyCommit:
            print(f"Repeats: {self.repeats}")
            with self.conn.cd(self.tsuite_path[0]): # we (unusually) cd into the test directory to run the tests
                for i in range(self.repeats):
                    result = self.conn.run("make", warn=True)
                    result = self.conn.run(f"timeout {self.timeout} ./testall", warn=True)
                    if result.failed:
                        # Makefile error - i.e. could compile but could not run tests
                        # Treat as a test failure - only really seen for APR (e.g. 0763586)
                        if result.return_code == 127:
                            self.maketestError = 2
                        else:
                            self.maketestError = result.return_code
                    self.exit_status_list.append(result.return_code)
