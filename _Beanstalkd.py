from fabric.api import *

# Analytics modules
from Container import Container


class Beanstalkd(Container):
    """ Beanstalkd class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if (self.offline):
            self.path = local("realpath 'repos/lighttpd1.4'", capture=True)
        else:
            self.path = '/home/beanstalkd'
            self.source_path = '/home/beanstalkd'
            # set timeout (in seconds) for the test suite to run
            self.timeout = 60

        self.tsuite_path = ('testheap.c', 'testjobs.c',
                            'testserv.c', 'testutil.c',
                            'heap-test.c', 'integ-test.c',
                            'job-test.c', 'util-test.c',
                            'tests', 'sh-tests',
                            'ct')
        self.ignore_coverage_from = ('/usr/include/*', )


    def compile(self):
        """ compile Beanstalkd """
        with cd(self.path):
            with settings(warn_only=True):
                result = run('git rev-list 6595102 | grep $(git rev-parse HEAD)')
                if result.succeeded:
                    pass # TODO: how to compile this thing?
                result = run('git rev-list b637898 ^e29be58 | grep $(git rev-parse HEAD)')
                if result.succeeded:
                    run("sed -i '/AC_PROG_LD/d' configure.in")
                result = run('git rev-list 78e76c3 | grep $(git rev-parse HEAD)')
                if result.succeeded:
                    run('bash buildconf.sh && ./configure')
                result = run('git rev-list e75696f ^78e76c3 | grep $(git rev-parse HEAD)')
                if result.succeeded:
                    # the developers got rid of autotools starting at fa96ec4
                    # thus the first two steps are needed only for older commtis
                    run('./autogen.sh && ./configure')
                result = run('git rev-list 4dc1586 ^880a218 | grep $(git rev-parse HEAD)')
                if result.succeeded:
                    run("git ls-files | xargs sed -i -e 's/dprintf/dbgprintf/g'")
                result = run('git rev-list $(git rev-parse HEAD) | grep d7e12a4')
                if result.succeeded:
                    run('rm -rf ct && cp -r /home/ct/ct .')
                #run("sed -i 's#tests/cutcheck: tests/cutcheck.o $(objects) $(tests:.c=.o)#tests/cutcheck: tests/cutcheck.o $(objects) $(tests:.c=.o); cc $(CFLAGS) tests/cutcheck.o $(objects) $(tests:.c=.o) -lcut -o tests/cutcheck#' Makefile");
                result = run("make CFLAGS='-O0 --coverage -Wl,--no-as-needed -levent -lrt' LDFLAGS='--coverage -Wl,--no-as-needed -levent -lrt'")
                if result.failed:
                    self.compileError = True


    def make_test(self):
        super(Beanstalkd, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False:
            with cd(self.path):
                with settings(warn_only=True):
                    result = run("make check CFLAGS='-D__LINUX__ -O0 --coverage -Wl,--no-as-needed -levent -lrt' LDFLAGS='--coverage -Wl,--no-as-needed -levent -lrt'")
                    if result.failed:
                        self.maketestError = result.return_code
                    
