from fabric import Connection

# Analytics modules
from Container import Container


class Vim(Container):
    """ Vim class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/vim'").stdout.strip()
        else:
            self.path = '/home/vim'
            self.source_path = '/home/vim/src'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 1500 # for revisions before 8.0.0000 400 suffices, later revs have more tests

        self.tsuite_path = ('src/testdir',)
        self.ignore_coverage_from = ('/usr/include/*',)

    def compile(self):
        """ compile Lighttpd """
        with self.conn.cd(self.path):
            # Run tests excluding gui tests (was default behaviour pre-8.0)
            result = self.conn.run("su regular -c \"CFLAGS='--coverage' LDFLAGS='--coverage' ./configure --without-x --disable-gtktest --with-features=normal --disable-gui\" && " +
                                   "su regular -c \"make -j`grep -c '^processor' /proc/cpuinfo`\"", warn=True)
            # make with as many jobs as there are cores
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Vim, self).make_test()
        # if compile failed, skip this step
        if not self.compileError:
            with self.conn.cd(self.path):
                    # Disable tests that fail locally but pass on Travis on latest revision (05a627c3d, Apr 2023)
                    # Unclear if container missing some dependency, test flaky (def. 'disassemble_closure_in_loop') or container issue (like mounting)
                    # Coverage and related metrics should be unaffected
                    result = self.conn.run(f"timeout -s SIGKILL {self.timeout} su regular -c 'export TEST_MAY_FAIL=Test_strftime,Test_opt_set_keycode,Test_set_completion,Test_disassemble_closure_in_loop && make test'", warn=True)
                    # SIGKILL due to subprocesses (su regular -c ...) not being killed by SIGTERM (a vim-only mem error, rev f4c5fcb)
                    if result.failed:
                        self.maketestError = result.return_code
