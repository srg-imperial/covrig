from fabric.api import *

# Analytics modules
from Container import Container


class Redis(Container):
    """ redis class """
    
    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        if (self.offline):
          self.path = local("realpath 'repos/redis'", capture=True)
        else:
          self.path = '/home/redis'
          self.source_path = '/home/redis/src'
          # set timeout (in seconds) for the test suite to run
          self.timeout = 600

        self.tsuite_path = ('tests',)
        self.ignore_coverage_from = ('/usr/include/*', )

    def compile(self):
        """ compile redis """
        with cd('/home/redis'):
           with settings(warn_only=True):
               run('chown -R regular:regular .')
               result = run('su regular -c \'make clean\' && su regular -c \'make gcov OPTIMIZATION=-O0\'')
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Redis, self).make_test()
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd('/home/redis/src'):
                with settings(warn_only=True):
                  for i in range(5):
                    result = run('su regular -c \'timeout ' + str(self.timeout) + ' make test\'')
                    if result.failed:
                        self.maketestError = result.return_code
                    run('killall redis')
