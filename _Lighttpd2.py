from fabric import Connection

# Analytics modules
from Container import Container


class Lighttpd2(Container):
    """ Lighttpd2 class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.conn.local("realpath 'repos/lighttpd2'", capture=True)
        else:
            self.path = '/home/lighttpd2'
            self.source_path = '/home/lighttpd2/src'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 200

        self.tsuite_path = ('tests', 'src/unittests')
        self.ignore_coverage_from = ('/usr/include/*', '/home/lighttpd2/src/unittests/*')

    def compile(self):
        """ compile Lighttpd """
        with self.conn.cd(self.path):
            result = self.conn.run('git rev-list 772e66b91c0c371f5777d50703b3629caa770e6e | grep $(git rev-parse HEAD)',
                                   warn=True)
            if result.ok:
                self.conn.run('apt-get -y remove libev4 libev-dev', warn=True)
                # run('wget http://dist.schmorp.de/libev/Attic/libev-3.9.tar.gz')
                with self.conn.cd('/root/libev-3.9'):
                    self.conn.run('sh configure && make install && ldconfig', warn=True)
            result = self.conn.run('sh autogen.sh && ' +
                                   'sh configure --with-lua --with-openssl --with-zlib --with-bzip2 &&' +
                                   " make -j3 CFLAGS='-fprofile-arcs -ftest-coverage -O0 -lm -std=c99' "
                                   + "LDFLAGS='-fprofile-arcs -ftest-coverage'", warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Lighttpd2, self).make_test()
        # if compile failed, skip this step
        if not self.compileError:
            with self.conn.cd(self.path):
                for i in range(5):
                    result = self.conn.run("timeout " + str(self.timeout) +
                                           " make check CFLAGS='-fprofile-arcs -ftest-coverage -O0 " +
                                           "-lm -std=c99' LDFLAGS='-fprofile-arcs -ftest-coverage'", warn=True)
                    if result.failed:
                        self.maketestError = result.return_code
