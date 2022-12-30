from fabric import Connection

# Analytics modules
from Container import Container


class Memcached(Container):
    """ Memcached class """

    # note that since sometimes memcached doesn't like us to be root,
    # a user account 'regular' is needed to run the following

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)
        # TODO: supply args to conn? maybe _init args? (bottom comment https://stackoverflow.com/questions/10280984/how-to-set-the-working-directory-for-a-fabric-task)
        # TODO: maybe as comment says it's to do with the "regular" user account?
        # set variables
        if self.offline:
            self.path = self.conn.local("realpath 'repos/memcached'", capture=True)
        else:
            self.path = '/home/memcached'
            self.source_path = '/home/memcached'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 200
        self.tsuite_path = ('t', 'testapp.c')

    def compile(self):
        """ compile Memcached """
        with self.conn.cd(self.source_path):
            # prior to acb84f05e0a8dc67a572dc647071002f9e64499d libevent1 is required
            result = self.conn.run(
                "git rev-list acb84f05e0a8dc67a572dc647071002f9e64499d | grep $(git rev-parse HEAD)"
                .format(self.source_path), warn=True)
            if result.ok:
                self.conn.run("apt-get -y install libevent1-dev", warn=True)
            # result = self.conn.run(('su regular -c ./autogen.sh && su regular -c ./configure && ' +
            #                         'su regular -c \'make clean\' && ' +
            #                         'su regular -c \"make CFLAGS+=\'-fprofile-arcs -ftest-coverage -g -O0 -pthread\'\"'), warn=True)
            # result = self.conn.run(('./autogen.sh && ./configure && make clean && \"make CFLAGS+=\'-fprofile-arcs -ftest-coverage -g -O0 -pthread\'\"'), warn=True)
            # result = self.conn.run('ls && ./configure && make clean && \"make CFLAGS+=\'-fprofile-arcs -ftest-coverage -g -O0 -pthread\'\"', warn=True)
            result = self.conn.run('./configure && make clean && make CFLAGS+=\'-fprofile-arcs -ftest-coverage -g -O0 -pthread\'', warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        super(Memcached, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if not self.compileError:
            with self.conn.cd(self.source_path):
                for i in range(5):
                    result = self.conn.run('su regular -c \'timeout ' + str(self.timeout) + ' make test\'', warn=True)
                    if result.failed:
                        self.maketestError = result.return_code
                    self.conn.run('killall memcached', warn=True)
