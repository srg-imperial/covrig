from fabric.api import *

from Container import Container


class Dovecot(Container):
    """ Dovecot class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if (self.offline):
            self.path = local("realpath 'repos/dovecot-2.2'", capture=True)
        else:
            self.path = '/home/dovecot-2.2'
            self.source_path = '/home/dovecot-2.2/src'
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
        with cd(self.path):
           with settings(warn_only=True):
               result = run("sh autogen.sh && " +
                            "sh configure CFLAGS='--coverage -O0' LDFLAGS='--coverage' && " +
                            "make -j`grep -c '^processor' /proc/cpuinfo`")
               if result.failed:
                   self.compileError = True

    def make_test(self):
        super(Dovecot, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd(self.path):
                with settings(warn_only=True):
                    result = run("timeout " + str(self.timeout) +
                                 " make check")
                    if result.failed:
                        self.maketestError = result.return_code
