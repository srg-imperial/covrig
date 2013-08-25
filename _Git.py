from fabric.api import *

# Analytics modules
from Container import Container


class Git(Container):
    """ Git class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)

        # set variables
        self.path = '/home/git'
        self.source_path = '/home/git'
        self.tsuite_path = ('/home/git/t',)
        # set timeout (in seconds) for the test suite to run
        self.timeout = 7200

    def compile(self):
        """ compile Zeromq """
        with cd(self.path):
           with settings(warn_only=True):
               result = run(('make configure && ./configure'))
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd(self.path):
                with settings(warn_only=True):
                    result = run(("timeout " + str(self.timeout) + 
                                  " make -j4 coverage"))
                    if result.failed:
                        self.maketestError = result.return_code
