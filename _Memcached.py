from fabric import Connection

# Analytics modules
from Container import Container


class Memcached(Container):
    """ Memcached class """

    # note that since sometimes memcached doesn't like us to be root,
    # a user account 'regular' is needed to run the following

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)
        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/memcached'").stdout.strip()
        else:
            self.path = '/home/memcached'
            self.source_path = '/home/memcached'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 600
        self.tsuite_path = ('t', 'testapp.c')

    def compile(self):
        """ compile Memcached """
        with self.conn.cd(self.source_path):
            # prior to acb84f05e0a8dc67a572dc647071002f9e64499d libevent1 is required
            result = self.conn.run("git rev-list acb84f05e0a8dc67a572dc647071002f9e64499d | grep $(git rev-parse HEAD)", warn=True)
            if result.stdout.strip() != "":
                self.conn.run("apt-get -y install libevent1-dev", warn=True)
            result = self.conn.run(('su regular -c ./autogen.sh && su regular -c ./configure && ' +
                                    'su regular -c \'make clean\' && ' +
                                    'su regular -c \"make CFLAGS+=\'-fprofile-arcs -ftest-coverage -g -O0 -pthread\'\"'), warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        super(Memcached, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if not self.compileError:
            with self.conn.cd(self.source_path):
                # for i in range(5):
                result = self.conn.run('su regular -c \'timeout ' + str(self.timeout) + ' make test\'', warn=True)
                if result.failed:
                    self.maketestError = result.return_code
                self.conn.run('killall memcached', warn=True)
