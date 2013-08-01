from __future__ import division
from fabric.api import *

# Analytics modules
from DataHandler import *


class Container(object):
    """ Class used to spawn a new container with sshd listening """

    def __init__(self, _image, _user, _pwd):
        self.image = _image
        self.user = _user
        self.pwd = _pwd
        # no errors yet :)
        self.compileError = False
        self.maketestError = False

    # The following are methods used to spawn a new container
    #

    def sshd_up(self):
        """ set up sshd """
        self.cnt_id = local('docker run -d -p 22 ' + self.image + 
                            ' /usr/sbin/sshd -D', capture=True)
        
    def set_ip(self):
        """ set container ID """
        self.ip = local("docker inspect " + self.cnt_id + 
                        " | grep IPAddress | awk '{print $2}'", capture=True)
        self.ip = self.ip.strip(',"')

    def fabric_setup(self):
        """ set fabric env parameters """
        env.user = self.user
        env.password = self.pwd
        env.host_string = self.ip

    def run_test(self):
        """ uname to check everything works """
        run('uname -on')

    def spawn(self):
        """ call all the methods needed to spawn a container """
        self.sshd_up()
        self.set_ip()
        self.fabric_setup()
        # create a ~/data/program-name directory where data will be collected
        local('mkdir -p data/' + self.__class__.__name__)

    def halt(self):
        """ shutdown the current container """
        print '\n\nHalting the current container...\n\n'
        local('docker stop ' + self.cnt_id)

    # The following are methods used to perform actions common to several containers
    #

    def get_commit_list(self, commits_no):
        """ get the list of the commits to be analyzed """
        # get the log list; the perl one-liner is to get rid of the damn colored output
        commit_list = run('cd ' + self.source_path + ' && git log -' + 
                          str(commits_no) + " --format=%h__%ct__%an | perl -pe 's/\e\[?.*?[\@-~]//g' ")
        return commit_list.splitlines()

    def count_sloc(self, path):
        """ use cloc to get the static lines of code for any given file or directory """
        lines = 0
        for p in path:
            lines += int(run("cloc " + p + " | tail -2 | awk '{print $5}'"))
        return str(lines)
            
    def checkout(self, revision):
        """ checkout the revision we want """
        with cd(self.path):
            # set the revision for current execution (commit sha)
            self.current_revision = revision
            # checkout revision
            run('git checkout ' + revision) 

    def backup(self, commit):
        """ create a tar.gz with all the .gcda and .gcno files and save it to localhost """
        with cd(self.path):
            cnid = 'coverage-' + commit
            run('mkdir ' + cnid)
            # find all the gcno/gcda files and copy them to ~/coverage-xxxxx/
            run("find . -iname '*.gcno' | xargs -I '{}' cp {} " + cnid)
            run("find . -iname '*.gcda' | xargs -I '{}' cp {} " + cnid)
            # save gcov/gcc/g++ info
            with cd(cnid):
                run('gcov -v | head -1 > build_info.txt')
                run('echo >> build_info.txt')
                run('gcc -v &>> build_info.txt')
                # don't raise any error if g++ is not installed 
                with settings(warn_only=True):
                    run('echo >> build_info.txt')
                    run('g++ -v &>> build_info.txt')
            # create an archive
            run('tar -cjf ' + cnid + '.tar.bz2 ' + cnid)
            # scp to localhost/data (get <remote path> , <local path>)
            get(cnid + '.tar.bz2', 'data/' + self.__class__.__name__ + '/' + cnid + '.tar.bz2')
            
    def overall_coverage(self):
        """ collect overall coverage results """
        if self.compileError == False and self.maketestError != 1:
            with cd(self.source_path):
                run('gcov * | tail -1 > coverage.txt', quiet=True) 

    def patch_coverage(self):
        """ compute the coverage for the current commit """
        self.edited_lines = 0
        self.covered_lines = 0
        self.average = 0

        # get a list of the changed files for the current commit
        with cd(self.path):
            changed_files = run("git show --pretty='format:' --name-only | perl -pe 's/\e\[?.*?[\@-~]//g'")
            # check didn't return an empty set
            if changed_files:
                # for every changed file, get the line numbers
                for f in changed_files.split('\r\n'):
                    # we're interested only in c/cpp files
                    extension = f.split('.')
                    # if the file doesn't have any extension, exit
                    if len(extension) < 2:
                        return
                    if extension[1] == 'c' or extension[1] == 'cpp':
                        line_numbers = run("git blame --porcelain " + f + " | grep " + 
                                           self.current_revision + " | awk '{print $2}'")
                        # check every line with its .gcov equivalent
                        for l in line_numbers.split('\r\n'):
                            cov = run("cat " + f + ".gcov | grep ' " + l + ":' | awk '{print $1}'")
                            # line is actual code, not covered
                            if cov == '#####:':
                                self.edited_lines += 1
                            # line is actual code, thus has been covered :)
                            elif cov != '-:':
                                self.covered_lines += 1
                                self.edited_lines += 1
                    else:
                        print extension[1] + ': we are not interested in this kind of file\n'
            # no file changed
            else:
                print '\nNo files changed (?)'
        # save results
        if self.covered_lines != 0:
            self.average = round(self.covered_lines/self.edited_lines, 3)*100

    def collect(self, author_name, timestamp):
        """ create a Collector to collect all info and a XMLHandler to parse them """
        c = Collector()
        # the class name which is actually running this method, as a string
        c.name = self.__class__.__name__
        # fill in some info about the test
        c.revision = self.current_revision
        c.author_name = author_name
        c.timestamp = timestamp
        # compute test suite size as SLOC. Note tsuite_path MUST be a tuple!
        c.tsuite_size = self.count_sloc(self.tsuite_path)
        # if compilation failed
        if self.compileError == True:
            c.compileError = True
        # if the test suite failed (i.e. the test suite is broken or cannot be run)
        elif self.maketestError == 1:
            c.maketestError = True
        # proceed in all other cases
        else:
            # fill patch coverage results
            c.edited_lines = self.edited_lines
            c.covered_lines = self.covered_lines
            c.average = self.average 
            # fill overall coverage results and exit status
            c.summary = run('cat ' + self.source_path + '/coverage.txt')
            c.compileError = self.compileError
            c.maketestError = self.maketestError

        # pass the Collector() obj to the Data Handler to store results in CSV format
        x = DataHandler(c)
        x.extractData()
        x.dumpCSV()
