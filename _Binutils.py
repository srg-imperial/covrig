from fabric import Connection

# Analytics modules
from Container import Container


class Binutils(Container):
    """ Binutils class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if self.offline:
            self.path = self.omnirun("realpath 'repos/binutils'").stdout.strip()
        else:
            self.path = '/home/binutils'
            self.source_path = '/home/binutils/binutils'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 60

        self.tsuite_path = ('binutils/testsuite', )
        self.limit_changes_to = ('binutils', )
        self.ignore_coverage_from = ('include/*' ,)

    def compile(self):
        """ compile Binutils """
        with self.conn.cd(self.path):
            result = self.conn.run("git rev-list b4d9e28e1d437c396461834f79be6cf0f2adc115 | grep $(git rev-parse HEAD)", warn=True)
            if result.stdout.strip() != "":
                # fix a bug that stops compilation for certain commits
                self.conn.run("sed -i -e 's/@colophon/@@colophon/' -e 's/doc@cygnus.com/doc@@cygnus.com/' bfd/doc/bfd.texinfo", warn=True)
                self.conn.run("sed -i -e 's/@colophon/@@colophon/' -e 's/doc@cygnus.com/doc@@cygnus.com/' ld/ld.texinfo",warn=True)
                self.conn.run('sed -i -e "s/@itemx --output-mach=@var/@item --output-mach=@var/g" -e "s/@itemx --input-type=@var{type}/@item --input-type=@var{type}/g" -e "s/@itemx --output-type=@var{type}/@item --output-type=@var{type}/g" binutils/doc/binutils.texi', warn=True)
            result = self.conn.run('./configure --disable-doc && make -j2 CFLAGS=\"-O0 -coverage -Wno-error\" LDFLAGS=\"-coverage\"', warn=True)
            if result.failed:
                self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Binutils, self).make_test()
        # if compile failed, skip this step
        if not self.compileError and not self.emptyCommit:
            with self.conn.cd(self.source_path):
                result = self.conn.run("timeout " + str(self.timeout) + " make check CFLAGS=\"-coverage -O0\" LDFLAGS=\"-coverage\"", warn=True)
                if result.failed:
                    self.maketestError = result.return_code
