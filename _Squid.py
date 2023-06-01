from fabric import Connection

# Analytics modules
from Container import Container


class Squid(Container):
    """ squid class """

    def __init__(self, _image, _user, _pwd, _repeats):
        Container.__init__(self, _image, _user, _pwd, _repeats)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/squid'").stdout.strip()
        else:
            self.path = '/home/squid'
            self.source_path = '/home/squid/src'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 90

        self.tsuite_path = ('test-suite',)
        self.skip_gen_for = "src/ipc/mem/.libs/*.gcno"

    def compile(self):
        """ compile Squid """
        with self.conn.cd(self.path):
            result = self.conn.run("sh bootstrap.sh && " +
                                   "sh configure CFLAGS='--coverage' CXXFLAGS='--coverage' LDFLAGS='--coverage' && " +
                                   "make -j`grep -c '^processor' /proc/cpuinfo` && " +
                                   f"rm -rf {self.skip_gen_for}", warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Squid, self).make_test()
        # if compile failed, skip this step
        if not self.compileError:
            print(f"Repeats: {self.repeats}")
            with self.conn.cd(self.path):
                for i in range(self.repeats):
                    result = self.conn.run('timeout ' + str(self.timeout) + ' make check', warn=True)
                    if result.failed:
                        self.maketestError = result.return_code
                    self.exit_status_list.append(result.return_code)
