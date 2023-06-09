from fabric import Connection

# Analytics modules
from Container import Container


class Git(Container):
    """ Git class """

    def __init__(self, _image, _user, _pwd, _repeats):
        Container.__init__(self, _image, _user, _pwd, _repeats)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/git'").stdout.strip()
        else:
            self.path = '/home/git'
            self.source_path = '/home/git'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 8000

        self.tsuite_path = ('t', 'test-*')
        self.ignore_coverage_from = ('/usr/include/*', )

    def compile(self):
        """ compile Git """
        with self.conn.cd(self.path):
            # attempt to speed up by setting multiple jobs -
            # tested on a multitude of revisions and is consistent - we can run the test suite in parallel without any
            # issues. Speedup min. 2x (all coverage archives produced w/o this though for consistency, speedup helpful
            # for identifying non-deterministic tests)
            result = self.conn.run('sed -i "s/DEFAULT_TEST_TARGET=test -j1 test/DEFAULT_TEST_TARGET=test -j4 test/g" Makefile', warn=True)
            # for later versions, need -std=c99
            result = self.conn.run("make configure && ./configure CFLAGS='-std=c99' && make -j`grep -c '^processor' /proc/cpuinfo` coverage-compile", warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Git, self).make_test()
        # if compile failed, skip this step
        if not self.compileError:
            print(f"Repeats: {self.repeats}")
            with self.conn.cd(self.path):
                for i in range(self.repeats):
                    result = self.conn.run("timeout " + str(self.timeout) + " make coverage", warn=True)
                    if result.failed:
                        self.maketestError = result.return_code
                    self.exit_status_list.append(result.return_code)
