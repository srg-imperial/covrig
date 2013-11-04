from fabric.api import *

# Analytics modules
from Container import Container


class Lighttpd(Container):
    """ Lighttpd class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)
        
        # set variables
        self.path = '/home/lighttpd2'
        self.source_path = '/home/lighttpd2/src'
        self.tsuite_path = ('/home/lighttpd2/tests', '/home/lighttpd2/src/unittests')
        # set timeout (in seconds) for the test suite to run
        self.timeout = 200

  
    def compile(self):
        """ compile Lighttpd """
        with cd(self.path):
           with settings(warn_only=True):
               result = run(('sh autogen.sh && ' +
                             'sh configure --with-lua --with-openssl --with-zlib --with-bzip2 &&' +
                             " make -j3 CFLAGS='-fprofile-arcs -ftest-coverage -O0 -lm -std=c99' "
                             + "LDFLAGS='-fprofile-arcs -ftest-coverage'"))
               if result.failed:
                   self.compileError = True

    def make_test(self):
        """ run the test suite """
        super(Lighttpd, self).make_test()
        # if compile failed, skip this step
        if self.compileError == False: 
            with cd(self.path):
                with settings(warn_only=True):
                    result = run(('timeout ' + str(self.timeout) +
                                 " make check CFLAGS='-fprofile-arcs -ftest-coverage -O0 " +
                                 "-lm -std=c99' LDFLAGS='-fprofile-arcs -ftest-coverage'"))
                    if result.failed:
                        self.maketestError = result.return_code
                    # copy every gcno/gcda file in the src directory
                    #run("find . -iname *.gcno | xargs -I '{}' cp {} " + self.source_path)
                    #run("find . -iname *.gcda | xargs -I '{}' cp {} " + self.source_path)
                    