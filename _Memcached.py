from fabric.api import *

# Analytics modules
from Container import Container


class Memcached(Container):
    """ Memcached class """

    # note that since sometimes memcached doesn't like us to be root,
    # a user account 'manlio' is needed to run the following

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)
        
        # set variables
        self.path = '/home/memcached'
        self.source_path = '/home/memcached'
        self.tsuite_path = ('/home/memcached/t','/home/memcached/testapp.c')
        # set timeout (in seconds) for the test suite to run
        self.timeout = 200
  
    def compile(self):
        """ compile Memcached """
        with cd(self.source_path):
           with settings(warn_only=True):
               result = run(('su regular -c ./autogen.sh && su regular -c ./configure && ' + 
                             'su regular -c \'make clean\' && ' + 
                             'su regular -c \"make CFLAGS+=\'-fprofile-arcs -ftest-coverage -g -O0 -pthread\'\"'))
               if result.failed:
                   self.compileError = True

    def make_test(self):
        super(Memcached, self).make_test()
        """ run the test suite """
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd(self.source_path):
                with settings(warn_only=True):
                    result = run('su regular -c \'timeout ' + str(self.timeout) + ' make test\'') 
                    if result.failed:
                        self.maketestError = result.return_code
