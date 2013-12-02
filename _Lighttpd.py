from fabric.api import *

# Analytics modules
from Container import Container


class Lighttpd(Container):
    """ Lighttpd class """

    def __init__(self, _image, _user, _pwd):
        Container.__init__(self, _image, _user, _pwd)
        
        # set variables
        if (self.offline):
          self.path = local("realpath 'repos/lighttpd2'", capture=True)
        else:
          self.path = '/home/lighttpd2'
          self.source_path = '/home/lighttpd2/src'
          # set timeout (in seconds) for the test suite to run
          self.timeout = 200
        
        self.tsuite_path = ('tests', 'src/unittests')
        self.ignore_coverage_from = ('/usr/include/*', '/home/lighttpd2/src/unittests/*')

  
    def compile(self):
        """ compile Lighttpd """
        with cd(self.path):
           with settings(warn_only=True):
               result = run('git rev-list 772e66b91c0c371f5777d50703b3629caa770e6e | grep $(git rev-parse HEAD)')
               if result.succeeded:
                 run ('apt-get -y remove libev4 libev-dev')
                 #run('wget http://dist.schmorp.de/libev/Attic/libev-3.9.tar.gz')
                 with cd('/root/libev-3.9'):
                   run ('sh configure && make install && ldconfig')
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
                  for i in range(2):
                    result = run(('timeout ' + str(self.timeout) +
                                 " make check CFLAGS='-fprofile-arcs -ftest-coverage -O0 " +
                                 "-lm -std=c99' LDFLAGS='-fprofile-arcs -ftest-coverage'"))
                    if result.failed:
                        self.maketestError = result.return_code
                    # copy every gcno/gcda file in the src directory
                    #run("find . -iname *.gcno | xargs -I '{}' cp {} " + self.source_path)
                    #run("find . -iname *.gcda | xargs -I '{}' cp {} " + self.source_path)
                    
