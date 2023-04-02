from fabric import Connection

# Analytics modules
from Container import Container


class Lighttpd2(Container):
    """ Lighttpd2 class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.conn.local("realpath 'repos/lighttpd2'", capture=True).stdout.strip()
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
            # if before or on revision 772e66b91c0c371f5777d50703b3629caa770e6e, remove libev-dev and libev4
            result = self.conn.run('git rev-list 772e66b91c0c371f5777d50703b3629caa770e6e | grep $(git rev-parse HEAD)',
                                   warn=True)
            if result.ok:
                self.conn.run('apt-get -y remove libev4 libev-dev', warn=True)
                with self.conn.cd('/root'):
                    self.conn.run('apt-get install wget && wget http://dist.schmorp.de/libev/Attic/libev-3.9.tar.gz')
                    self.conn.run('tar -xvf libev-3.9.tar.gz')
                    self.conn.run('cd libev-3.9 && sh configure && make install && ldconfig', warn=True)
            # remove -Werror from configure.ac since we're just trying to get coverage data, not ship code
            self.conn.run('sed -i "s/-Werror\s//g" configure.ac', warn=True)
            # self.conn.run('sed -i "s/\s--quiet\"/\"/g" configure', warn=True)
            result = self.conn.run('sh autogen.sh && ' +
                                   'sh configure --with-lua --with-gnutls --with-openssl --with-zlib --with-bzip2 &&' +
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
