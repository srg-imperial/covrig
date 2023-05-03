import subprocess

from fabric import Connection

# Analytics modules
from Container import Container


class Lighttpd2(Container):
    """ Lighttpd2 class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/lighttpd2'").stdout.strip()
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
            if result.stdout.strip() != "":
                self.conn.run('apt-get -y remove libev4 libev-dev', warn=True)
                with self.conn.cd('/root'):
                    self.conn.run('apt-get install wget && wget http://dist.schmorp.de/libev/Attic/libev-3.9.tar.gz')
                    self.conn.run('tar -xvf libev-3.9.tar.gz')
                    self.conn.run('cd libev-3.9 && sh configure && make install && ldconfig', warn=True)
            # remove -Werror from configure.ac since we're just trying to get coverage data, not ship code
            self.conn.run('sed -i "s/-Werror\s//g" configure.ac', warn=True)

            # make tests run serially otherwise they will fail before this revision
            result = self.conn.run('git rev-list 92f0a5f237ed3235525c5d6f2280740fc49f775d | grep $(git rev-parse HEAD)', warn=True)
            if result.stdout.strip() != "":
                self.conn.run('sed -i "s/tar-ustar/tar-ustar serial-tests/g" configure.ac', warn=True)
            result = self.conn.run('sh autogen.sh && ' +
                                   'sh configure --with-lua --with-gnutls --with-openssl --with-zlib --with-bzip2', warn=True)

            # if before or on revision b9fadd3db3bd8a56d2508e61ddbfaadfb28516c2, make gnutls_record_uncork() take 2 arguments
            result = self.conn.run('git rev-list b9fadd3db3bd8a56d2508e61ddbfaadfb28516c2 | grep $(git rev-parse HEAD)', warn=True)
            if result.stdout.strip() != "":
                # make gnutls_record_uncork() take 2 arguments, I think this is a bug in the gnutls library/this version is too new for these revisions
                # May not do anything if the revision is too old, since gnutls_record_uncork() and gnutls_filter.c will not exist
                self.conn.run('sed -i "s/gnutls_record_uncork(f->session);/gnutls_record_uncork(f->session, 0);/g" src/modules/gnutls_filter.c', warn=True)
            result = self.conn.run("make -j3 CFLAGS='-fprofile-arcs -ftest-coverage -O0 -lm -std=c99' "
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
