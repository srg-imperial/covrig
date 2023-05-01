from fabric import Connection

# Analytics modules
from Container import Container


class BinutilsGdb(Container):
    """ BinutilsGdb class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/binutils'").stdout.strip()
        else:
            self.path = '/home/binutils'
            self.source_path = '/home/binutils/binutils'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 60

        self.tsuite_path = ('binutils/testsuite', )
        self.limit_changes_to = ('binutils', )
        self.ignore_coverage_from = ('include/*', )

    def compile(self):
        """ compile Binutils """
        with self.conn.cd(self.path):
            # We only care about the /binutils directory of the /binutils-gdb repo, so disable the rest (speeds up compilation and reduces dependencies)
            result = self.conn.run(
                './configure --disable-doc --disable-gdb --disable-gprof --disable-gprofng && make -j2 CFLAGS=\"-O0 -coverage -Wno-error\" LDFLAGS=\"-coverage\"',
                warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(BinutilsGdb, self).make_test()
        # if compile failed, skip this step
        if not self.compileError and not self.emptyCommit:
            with self.conn.cd(self.source_path):
                result = self.conn.run("timeout " + str(self.timeout) + " make check CFLAGS=\"-coverage -O0\" LDFLAGS=\"-coverage\"", warn=True)
                if result.failed:
                    self.maketestError = result.return_code
