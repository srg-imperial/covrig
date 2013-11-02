from fabric.api import *

# Analytics modules
from Container import Container


class Redis(Container):
    """ redis class """
    
    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        self.path = '/home/redis'
        self.source_path = '/home/redis/src'
        self.tsuite_path = ('/home/redis/tests',)
        # set timeout (in seconds) for the test suite to run
        self.timeout = 45

    def compile(self):
        """ compile redis """
        with cd('/home/redis'):
           with settings(warn_only=True):
               result = run('make clean && make gcov')
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Redis, self).make_test()
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd('/home/redis/src'):
                with settings(warn_only=True):
                    result = run('timeout ' + str(self.timeout) + ' make test')
                    if result.failed:
                        self.maketestError = result.return_code
