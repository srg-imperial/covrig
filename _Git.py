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
        self.tsuite_path = ('/home/git/t', '/home/git/test-*')
        # set timeout (in seconds) for the test suite to run
        self.timeout = 7200

    def compile(self):
        """ compile Git """
        with cd(self.path):
            with settings(warn_only=True):
                result = run(
                    ('make configure && ./configure && make -j4 coverage-compile'))
                if result.failed:
                    self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Git, self).make_test()
        # if compile failed, skip this step
        if not self.compileError:
            with cd(self.path):
                with settings(warn_only=True):
                    result = run(("timeout " + str(self.timeout) +
                                  " make coverage"))
                    if result.failed:
                        self.maketestError = result.return_code
