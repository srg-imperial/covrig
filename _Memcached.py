from fabric.api import *

# Analytics modules
from Container import Container


class Memcached(Container):

    """ Memcached class """

    # note that since sometimes memcached doesn't like us to be root,
    # a user account 'regular' is needed to run the following

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if (self.offline):
            self.path = local("realpath 'repos/memcached'", capture=True)
        else:
            self.path = '/home/memcached'
            self.source_path = '/home/memcached'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 200
        self.tsuite_path = ('t', 'testapp.c')

    def compile(self):
        """ compile Memcached """
        with cd(self.source_path):
            with settings(warn_only=True):
                # prior to acb84f05e0a8dc67a572dc647071002f9e64499d libevent1
                # is required
                result = run(
                    'git rev-list acb84f05e0a8dc67a572dc647071002f9e64499d | grep $(git rev-parse HEAD)')
                if result.succeeded:
                    run('apt-get -y install libevent1-dev')
                result = run(('su regular -c ./autogen.sh && su regular -c ./configure && ' +
                              'su regular -c \'make clean\' && ' +
                              'su regular -c \"make CFLAGS+=\'-fprofile-arcs -ftest-coverage -g -O0 -pthread\'\"'))
                if result.failed:
                    self.compileError = True

    def make_test(self):
        super(Memcached, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if not self.compileError:
            with cd(self.source_path):
                with settings(warn_only=True):
                    for i in range(5):
                        result = run(
                            'su regular -c \'timeout ' + str(self.timeout) + ' make test\'')
                        if result.failed:
                            self.maketestError = result.return_code
                        run('killall memcached')
