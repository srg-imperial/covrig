from fabric import Connection

# Analytics modules
from Container import Container


class Curl(Container):
    """ Curl class """

    # Inspired by https://github.com/curl/curl/blob/master/scripts/coverage.sh

    def __init__(self, _image, _user, _pwd, _repeats):
        Container.__init__(self, _image, _user, _pwd, _repeats)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/curl'").stdout.strip()
        else:
            self.path = '/home/curl'
            self.source_path = '/home/curl/cvr'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 600

        self.tsuite_path = ('tests',)
        self.ignore_coverage_from = ('include/*', '*/tests/*')

    def compile(self):
        """ compile Curl """
        with self.conn.cd(self.path):
            # For later revisions of curl, ignore restriction to lcov 1.13 since we are using 1.16
            result = self.conn.run(
                f"sed -i m4/ax_code_coverage.m4 -e 's/1.11 1.13/1.11 1.13 1.16/g'", warn=True)
            # create a directory for the coverage build (cvr)
            result = self.conn.run('autoreconf -fi && mkdir -p cvr', warn=True)
            # Disable certain tests that rely on curl -k and broken tests (1316, usually disabled in 82a4d53)
            result = self.conn.run(
                f"sed -i {self.path}/tests/Makefile.am -e 's/$(TEST) $(TEST_Q)/$(TEST) $(TEST_Q) !46 !310 !311 !312 !1026 !1316 !2034 !2035/g'",
                warn=True)
            with self.conn.cd('cvr'):
                result = self.conn.run('../configure --disable-shared --enable-debug --enable-maintainer-mode --enable-manual '
                                       '--enable-code-coverage --with-openssl CFLAGS="-fprofile-abs-path --coverage -g -O0" LDFLAGS="--coverage" && make -sj', warn=True)
                if result.failed:
                    self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Curl, self).make_test()
        # if compile failed, skip this step
        if not self.compileError and not self.emptyCommit:
            print(f"Repeats: {self.repeats}")
            with self.conn.cd(self.source_path):
                for i in range(self.repeats):
                    result = self.conn.run(f"export USER=root && timeout {self.timeout} make test", warn=True)
                    if result.failed:
                        self.maketestError = result.return_code
                    self.exit_status_list.append(result.return_code)
                self.conn.run('killall curl', warn=True)
