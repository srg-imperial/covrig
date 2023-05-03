from fabric import Connection

# Analytics modules
from Container import Container


class Dovecot(Container):
    """ Dovecot class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/dovecot'").stdout.strip()
        else:
            self.path = '/home/dovecot'
            self.source_path = '/home/dovecot/src'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 200

        self.tsuite_path = (
            'src/anvil/test-*',
            'src/auth/test-*',
            'src/director/test-*',
            'src/doveadm/dsync/test-*',
            'src/lib-test',
            'src/lib/test-*',
            'src/lib-storage/test-*',
            'src/lib-imap/test-*',
            'src/lib-mail/test-*',
            'src/lib-dict/test-*',
            'src/lib-index/test-*',
            'src/lib-http/test-*',
        )


    def compile(self):
        """ compile Dovecot """
        with self.conn.cd(self.path):
            self.conn.run("sed -i \"/^\s\swget/ s/$/ --no-check-certificate/\" autogen.sh")
            result = self.conn.run("sh autogen.sh && " +
                         "sh configure CFLAGS='--coverage -O0' LDFLAGS='--coverage' && " +
                         "make -j`grep -c '^processor' /proc/cpuinfo`", warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        super(Dovecot, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if not self.compileError:
            with self.conn.cd(self.path):
                result = self.conn.run("timeout " + str(self.timeout) + " make check")
                if result.failed:
                    self.maketestError = result.return_code
