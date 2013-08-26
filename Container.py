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
        env.host_string = self.ip + ':22'
	# in a perfect world, this would not be here
	env.connection_attempts = 10

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
        local('docker rm ' + self.cnt_id)

    # The following are methods used to perform actions common to several containers
    #

    def get_commit_list(self, commits_no):
        """ get the list of the commits to be analyzed """
        # get the log list; the perl one-liner is to get rid of the damn colored output
        commit_list = run('cd ' + self.source_path + ' && git log -' + 
                          str(commits_no) + " --format=%h__%ct__%an | "
                          + "perl -pe 's/\e\[?.*?[\@-~]//g' ")
        return commit_list.splitlines()

    def get_commit_custom(self, single_commit):
        """ attach timestamp and author to a given commit """
        commit = run('cd ' + self.source_path + ' && git show ' +
                          str(single_commit) + " --format=%h__%ct__%an | "
                          + "head -1 | perl -pe 's/\e\[?.*?[\@-~]//g' ", quiet=True)
        return commit

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
            with settings(warn_only=True):
                result = run('git checkout ' + revision) 
                if result.failed:
                    run('git stash && git checkout ' + revision)

    def tsize_compute(self):
        """ compute test suite as SLOCs """
        # rebuild the test suite with only files or dirs that 
        # actually exists in the current revision
        actual_tsuite = [ ]
        for item in self.tsuite_path:
            fileExists = run ('( [ -f ' + item + ' ] || [ -d ' + item + ' ] ) && echo y || echo n')
            if fileExists == 'y':
                actual_tsuite.append(item)
                print 'Added ' + item + ' to the test suite\n'
        self.tsuite_path = actual_tsuite 
        self.tsize = self.count_sloc(self.tsuite_path)

    def prepare_coverage(self):
        """ prepare the environment to run gcov """
        if self.compileError == True:
            return
        # mv the test suite so that it doesn't pollute coverage info
        for item in self.tsuite_path:
            run('mv ' + item + ' /home/')
        # move every gcda, gcno, c and cpp file to the mycoverage folder
        with cd(self.source_path):
            run('mkdir mycoverage')
            run("find . -iname '*.gcno' | xargs -I '{}' cp {} mycoverage")
            run("find . -iname '*.gcda' | xargs -I '{}' cp {} mycoverage")
            run("find . -iname '*.c' | xargs -I '{}' cp {} mycoverage")
            run("find . -iname '*.cpp' | xargs -I '{}' cp {} mycoverage")
    
    def backup(self, commit):
        """ create a tar.bz2 with all the .gcda and .gcno files and save it to localhost """
        if self.compileError == True:
            return
        with cd(self.source_path + '/mycoverage'):
            # save gcov/gcc/g++ info
            with settings(warn_only=True):
                run('gcov -v | head -1 > build_info.txt')
                run('echo >> build_info.txt')
                run('gcc -v &>> build_info.txt')
        with cd(self.source_path):
            # bzip all the coverage files
            run('cp -R mycoverage cov-' + commit)
            run('tar -cjf coverage-' + commit + '.tar.bz2 cov-' + commit)
            # scp to localhost/data
            get('coverage-' + commit + '.tar.bz2', 'data/' + self.__class__.__name__ + 
                '/' + 'coverage-' + commit + '.tar.bz2')
            
    def overall_coverage(self):
        """ collect overall coverage results """
        if self.compileError == True:
            return
        # run gcov to get overall coverage and ELOCs
        with cd(self.source_path + '/mycoverage'):
            run('gcov * | tail -1 > coverage.txt', quiet=True) 
        # mv the test suite back to its place
        with cd('/home'):
            with settings(warn_only=True):
                for item in self.tsuite_path:
                    i = item.split('/')
                    run('mv ' + i[-1] + ' ' + self.path)

    def patch_coverage(self):
        """ compute the coverage for the current commit """
        self.added_lines = 0
        self.covered_lines = 0
        self.uncovered_lines = 0
        self.average = 0

        if self.compileError == True:
            return
        # get a list of the changed files for the current commit
        with cd(self.path):
            changed_files = run("git show --pretty='format:' --name-only" + 
                                " | perl -pe 's/\e\[?.*?[\@-~]//g'")
            # check didn't return an empty set
            if changed_files:
                # for every changed file 
                for f in changed_files.split('\r\n'):
                    # get the filename
                    filename = f.split('/')
                    with cd(self.source_path + '/mycoverage'):
                        # check *.c.gcov exists
                        fileExists = run ('[ -f ' + filename[-1] + '.gcov ] && echo y || echo n')
                        if fileExists == 'y':
                            print 'Coverage information found\n'
                            # get the changed lines numbers
                            with cd(self.path):
                                line_numbers = run("git blame --porcelain " + f + 
                                                   " | grep " + self.current_revision 
                                                   + " | awk '{print $2}'")
                            # for every changed line
                            for l in line_numbers.split('\r\n'):
                                # increment added lines
                                self.added_lines += 1
                                # check if it has been covered
                                cov = run("cat " + filename[-1] + ".gcov | grep ' " + 
                                          l + ":' | awk '{print $1}'")
                                # uncovered line
                                if cov == '#####:':
                                    self.uncovered_lines += 1
                                # not(not executable), thus has been covered
                                elif cov != '-:':
                                    self.covered_lines += 1
                        # no .gcov information found
                        else:
                            print 'No coverage information found for ' + filename[-1] + '\n'
                            with cd(self.path):
                                # check if the file exists, here or in /home/
                                fileExists2 = run ('[ -f ' + f + ' ] && echo y || echo n')
                                if fileExists2 == 'y':
                                    self.added_lines += int(run("git blame --porcelain " + f + 
                                                            " | grep " + self.current_revision 
                                                            + " | awk '{print $2}' | wc -l"))
                                else:
                                    print 'No file found ' + f + '\n'
                # save results
                if self.covered_lines > 0:
                    self.average = round( ((self.covered_lines / (self.covered_lines +
                                                                  self.uncovered_lines)) 
                                           * 100), 2)

    def collect(self, author_name, timestamp):
        """ create a Collector to collect all info and a XMLHandler to parse them """
        c = Collector()
        # the class name which is actually running this method, as a string
        c.name = self.__class__.__name__
        # fill in some info about the test
        c.revision = self.current_revision
        c.author_name = author_name
        c.timestamp = timestamp
        c.tsuite_size = self.tsize
        # if compilation failed, halt
        if self.compileError == True:
            c.compileError = True
        # go on
        else:
            # fill patch coverage results
            c.added_lines = self.added_lines
            c.covered_lines = self.covered_lines
            c.uncovered_lines = self.uncovered_lines
            c.average = self.average 
            # fill overall coverage results and exit status
            with settings(warn_only=True):
                c.summary = run('cat ' + self.source_path + '/mycoverage/coverage.txt')
            c.compileError = self.compileError
            c.maketestError = self.maketestError

        # pass the Collector() obj to the Data Handler to store results in CSV format
        x = DataHandler(c)
        x.extractData()
        x.dumpCSV()
