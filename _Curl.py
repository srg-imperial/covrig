from fabric import Connection

# Analytics modules
from Container import Container


class Curl(Container):
    """ Curl class """

    # Inspired by https://github.com/curl/curl/blob/master/scripts/coverage.sh

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.conn.local("realpath 'repos/curl'", capture=True)
        else:
            self.path = '/home/curl'
            self.source_path = '/home/curl/cvr'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 600

        self.tsuite_path = ('tests',)
        self.ignore_coverage_from = ('include/*',)

    def compile(self):
        """ compile Curl """
        with self.conn.cd(self.path):
            # create a directory for the coverage build (cvr)
            result = self.conn.run('autoreconf -fi && mkdir -p cvr', warn=True)
            with self.conn.cd('cvr'):
                result = self.conn.run('../configure --disable-shared --enable-debug --enable-maintainer-mode '
                                       '--enable-code-coverage --with-openssl && make -sj  CFLAGS="-fprofile-arcs -ftest-coverage" LDFLAGS="-lgcov --coverage"', warn=True)
                if result.failed:
                    self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Curl, self).make_test()
        # if compile failed, skip this step
        if not self.compileError and not self.emptyCommit:
            with self.conn.cd(self.source_path):
                # make TFLAGS=-n test-nonflaky for later revisions, but will do make test for general coverage
                result = self.conn.run(f"export USER=root && timeout {self.timeout} make test", warn=True)
                if result.failed:
                    self.maketestError = result.return_code
