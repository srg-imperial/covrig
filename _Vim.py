from fabric.api import *

# Analytics modules
from Container import Container


class Vim(Container):
    """ Vim class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)
        
        # set variables
        if (self.offline):
          self.path = local("realpath 'repos/vim'", capture=True)
        else:
          self.path = '/home/vim'
          self.source_path = '/home/vim/src'
          # set timeout (in seconds) for the test suite to run
          self.timeout = 200
        
        self.tsuite_path = ('src/testdir')
        self.ignore_coverage_from = ('/usr/include/*', )

  
    def compile(self):
        """ compile Lighttpd """
        with cd(self.path):
           with settings(warn_only=True):
               result = run(("CFLAGS='--coverage' LDFLAGS='--coverage' ./configure --without-x && " +
                             "make -j`grep -c '^processor' /proc/cpuinfo`"))
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Vim, self).make_test()
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd(self.path):
                with settings(warn_only=True):
                    result = run('make test', pty=False, timeout=self.timeout)
                    if result.failed:
                        self.maketestError = result.return_code
 
