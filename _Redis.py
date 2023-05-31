from fabric import Connection

# Analytics modules
from Container import Container


class Redis(Container):
    """ redis class """

    def __init__(self, _image, _user, _pwd, _repeats):
        Container.__init__(self, _image, _user, _pwd, _repeats)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/redis'").stdout.strip()
        else:
            self.path = '/home/redis'
            self.source_path = '/home/redis/src'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 1200

        self.tsuite_path = ('tests',)
        self.ignore_coverage_from = ('/usr/include/*', )

    def compile(self):
        if self.offline:
            # Shouldn't get here as compile is only done if we're online
            self.path = self.conn.local("realpath 'repos/redis'").stdout
        """ compile redis """
        with self.conn.cd(self.path):
            self.conn.run('chown -R regular:regular .', warn=True)
            result = self.conn.run(f'su regular -c \'make clean\' && su regular -c \'make gcov OPTIMIZATION=-O0 CFLAGS=-std=gnu99\'', warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Redis, self).make_test()
        # if compile failed, skip this step
        if not self.compileError:
            print(f"Repeats: {self.repeats}")
            with self.conn.cd(self.source_path):
                for i in range(self.repeats):
                    result = self.conn.run('su regular -c \'timeout ' + str(self.timeout) + ' make test\'', warn=True)
                    if result.failed:
                        self.maketestError = result.return_code
                    self.exit_status_list.append(result.return_code)
                self.conn.run('killall redis', warn=True)
