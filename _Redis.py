from fabric.api import *

# Analytics modules
from Container import Container


class Redis(Container):
    """ redis class """
    
    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

    def compile(self):
        """ compile redis """
        with cd('/home/redis'):
           with settings(warn_only=True):
               result = run('make clean && make gcov')
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd('/home/redis/src'):
                with settings(warn_only=True):
                    result = run('make test')
                    if result.failed:
                        self.maketestError = result.return_code
