from __future__ import division
from fabric.api import *
import fnmatch

# Analytics modules
from DataHandler import *


class Container(object):
    """ Class used to spawn a new container with sshd listening """

    class LineType:
        NotCovered = 1
        NotExecutable = 2
        Covered = 3

    def __init__(self, _image, _user, _pwd):
        self.image = _image
        self.user = _user
        self.pwd = _pwd
        # no errors yet :)
        self.compileError = False
        self.maketestError = False
        """ how many lines from previous patches are covered now """
        self.changed_files = []
        self.echanged_files = []
        self.uncovered_lines_list = []
        self.prev_covered = []
        self.hunkheads = []
        self.ehunkheads = []
        self.hunkheads3 = []
        self.ehunkheads3 = []

        #split the test suite into directories and files
        self.tsuite_dir = []
        self.tsuite_file = []

        self.changed_test_files = []
        self.merge = False;
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
                          str(commits_no) + " --first-parent --format=%h__%ct__%an | "
                          + "perl -pe 's/\e\[?.*?[\@-~]//g' ")
        return commit_list.splitlines()

    def get_commit_custom(self, single_commit, lookbehind):
        """ attach timestamp and author to a given commit """
        current_commit = run('cd ' + self.source_path + ' && git rev-parse HEAD')
        run('cd ' + self.source_path + ' && git checkout ' + single_commit)
        commit_list = self.get_commit_list(lookbehind);

        run('cd ' + self.source_path + ' && git checkout ' + current_commit)
        return commit_list

    def count_sloc(self, path):
        """ use cloc to get the static lines of code for any given file or directory """
        lines = 0
        for p in path:
            try:
              lines += int(run("cloc " + p + " | tail -2 | awk '{print $5}'"))
            except ValueError:
              lines += int(run("wc -l " + p + "/*|tail -1|awk '{ print $1 }'"))
        return str(lines)

    def count_hunks(self, prev_revision):
      with cd(self.path):
        changed = run("git diff -b -U0 " +
                       prev_revision + " " + self.current_revision +
                       " | perl -pe 's/\e\[?.*?[\@-~]//g'")
        if changed:
          self.hunkheads = [i for i in changed.split('\r\n') if i.startswith( '@@' )]
          changed = run("git diff -b " +
                         prev_revision + " " + self.current_revision +
                         " | perl -pe 's/\e\[?.*?[\@-~]//g'")
          self.hunkheads3 = [i for i in changed.split('\r\n') if i.startswith( '@@' )]

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
            self.is_merge(revision)

    def tsize_compute(self):
        """ compute test suite as SLOCs """
        # rebuild the test suite with only files or dirs that 
        # actually exists in the current revision
        actual_tsuite = [ ]
        for item in self.tsuite_path:
            fileExists = run ('ls -U ' + item + ' >/dev/null 2>&1 && echo y || echo n')
            if fileExists == 'y':
                actual_tsuite.append(item)
                print 'Added ' + item + ' to the test suite\n'
                isdir = run ('[ -d "' + item + '" ] && echo y || echo n')
                if isdir == 'y':
                  self.tsuite_dir.append(item)
                else:
                  self.tsuite_file.append(item)
        self.tsuite_path = actual_tsuite 
        #XXX count_sloc will fail if a wildcard path contains no files recognized by cloc
        self.tsize = self.count_sloc(self.tsuite_path)

    def backup(self, commit):
        """ create a tar.bz2 with all the .gcda and .gcno files and save it to localhost """
        if self.compileError == True:
            return
        with cd(self.source_path):
            # save gcov/gcc/g++ info
            with settings(warn_only=True):
                run('gcov -v | head -1 > build_info.txt')
                run('echo >> build_info.txt')
                run('gcc -v &>> build_info.txt')
        with cd(self.source_path):
            # bzip all the coverage files
            run("find . -name '*.gcov' > gcovlist")
            run('tar -cjf coverage-' + commit + '.tar.bz2 -T gcovlist')
            # scp to localhost/data
            get('coverage-' + commit + '.tar.bz2', 'data/' + self.__class__.__name__ + 
                '/' + 'coverage-' + commit + '.tar.bz2')
    
    def stash_tests(self, pop = False):
        if pop:
            with cd('/home'):
                with settings(warn_only=True):
                    for item in self.tsuite_path:
                        i = item.split('/')
                        ent = i[-1]
                        i[-1] = ""
                        p = "/".join(i)
                        run('mv ' + ent + ' ' + p)
        else:
            for item in self.tsuite_path:
                run('mv ' + item + ' /home/')

    def rec_initial_coverage(self):
        self.stash_tests()
        with cd(self.source_path):
            run('lcov -c -i -d . -o base.info')
        self.stash_tests(True)

    def make_test(self):
        if self.compileError:
            return
        self.rec_initial_coverage()

    def overall_coverage(self):
        """ collect overall coverage results """
        if self.compileError == True:
            return
        self.stash_tests()
        # run gcov to get overall coverage and ELOCs
        with cd(self.source_path):
            run('lcov -c -d . -o test.info', quiet=True)
            run("lcov -a base.info -a test.info -o total.info |tail -3|head -1| sed -e 's/[^0-9]*//' -e 's/([0-9]*//' > coverage.txt");
            run('find -name "*.gcda"|xargs gcov', quiet=True)

        self.stash_tests(True)

    def is_covered(self, filepath, line):
        filename = filepath.split('/')
        with cd(self.source_path):
            fileExists = run ('[ -f ' + filename[-1] + '.gcov ] && echo y || echo n')
            if fileExists == 'y':
              cov = run("cat " + filename[-1] + ".gcov | grep ':[ ]*" +
                  line + ":' | awk 'BEGIN { FS = \":\" } ; {print $1}'")
              cov = cov.strip()
              if cov == '#####' or cov == '=====':
                return self.LineType.NotCovered
              elif cov == '-':
                return self.LineType.NotExecutable
              else:
                return self.LineType.Covered
            else:
              return self.LineType.NotExecutable

    def is_merge(self, commit):
      with cd(self.path):
        mergestatus = run("git show " + commit + "|head -2|tail -1")
        self.merge = mergestatus.startswith("Merge:")
        return self.merge

    def patch_coverage(self, prev_revision):
        """ compute the coverage for the current commit """
        self.added_lines = 0
        self.covered_lines = 0
        self.uncovered_lines = 0
        self.average = 0

        # get a list of the changed files for the current commit
        with cd(self.path):
            changed_files = run("git diff -b --pretty='format:' --name-only " +
                                prev_revision + " " + self.current_revision +
                                " | perl -pe 's/\e\[?.*?[\@-~]//g'")
            if changed_files:
                self.changed_files = [i for i in changed_files.split('\r\n') if i]
                # for every changed file 
                for f in self.changed_files:
                    # get the filename
                    self.uncovered_lines_list.append([])
                    if self.compileError == False:
                      #check whether it's a test file
                      with cd(self.path):
                        fileExists = run('[ -f ' + f + ' ] && echo y || echo n')
                        if fileExists == 'y':
                          realp = run('realpath ' + f)
                          for tf in self.tsuite_file:
                            if fnmatch.fnmatch(realp, tf):
                              self.changed_test_files.append(f)
                          for td in self.tsuite_dir:
                            if realp.startswith(td + "/"):
                              self.changed_test_files.append(f)
                      self.changed_test_files = list(set(self.changed_test_files))
                      with cd(self.source_path):
                        # check *.c.gcov exists
                        filename = f.split('/')
                        fileExists = run ('[ -f ' + filename[-1] + '.gcov ] && echo y || echo n')
                        if fileExists == 'y':
                            print 'Coverage information found\n'
                            self.echanged_files.append(f)
                            # get the changed lines numbers
                            with cd(self.path):
                                line_numbers = run("/root/measure-cov.sh " + prev_revision + " " + self.current_revision + " " + f)
                                file_diff = run("git diff -b -U0 " +
                                                prev_revision + " " + self.current_revision +
                                                " -- " + f +
                                                " | perl -pe 's/\e\[?.*?[\@-~]//g'")
                                self.ehunkheads += [i for i in file_diff.split('\r\n') if i.startswith('@@')]
                                file_diff3 = run("git diff -b " +
                                                prev_revision + " " + self.current_revision +
                                                " -- " + f +
                                                " | perl -pe 's/\e\[?.*?[\@-~]//g'")
                                self.ehunkheads3 += [i for i in file_diff3.split('\r\n') if i.startswith('@@')]
                            # for every changed line
                            for l in line_numbers.split('\r\n'):
                                # increment added lines
                                self.added_lines += 1
                                # check if it has been covered
                                cov = run("cat " + filename[-1] + ".gcov | grep ':[ ]*" + 
                                    l + ":' | awk 'BEGIN { FS = \":\" } ; {print $1}'")
                                cov = cov.strip()
                                # uncovered line
                                if cov == '#####' or cov == '=====':
                                    self.uncovered_lines += 1
                                    self.uncovered_lines_list[-1].append(l)
                                # not(not executable), thus has been covered
                                elif cov != '-':
                                    self.covered_lines += 1
                        # no .gcov information found
                        else:
                            # most likely the file was not compiled into any of the programs
                            # executed by the test suite. Alternatives include: file was removed, program crashed or has no permissions
                            print 'No coverage information found for ' + filename[-1] + '\n'

                            with cd(self.path):
                              fileExists = run ('[ -f ' + f + ' ] && echo y || echo n')
                              if fileExists == 'y':
                                line_numbers = run("/root/measure-cov.sh " + prev_revision + " " + self.current_revision + " " + f)
                                lines = line_numbers.split('\r\n')
                                self.added_lines += len(lines)
                                file_diff = run("git diff -b -U0 " +
                                                prev_revision + " " + self.current_revision +
                                                " -- " + f +
                                                " | perl -pe 's/\e\[?.*?[\@-~]//g'")
                                # check if the file was compiled (but not executed)
                                with cd(self.source_path):
                                  executableinfo = run ( "sed -n '/SF:.*" + filename[-1] + "/,/end_of_record/p' base.info")
                                  if executableinfo:
                                    self.echanged_files.append(f)
                                    self.ehunkheads += [i for i in file_diff.split('\r\n') if i.startswith('@@')]
                                    file_diff3 = run("git diff -b " +
                                                    prev_revision + " " + self.current_revision +
                                                    " -- " + f +
                                                    " | perl -pe 's/\e\[?.*?[\@-~]//g'")
                                    self.ehunkheads3 += [i for i in file_diff3.split('\r\n') if i.startswith('@@')]
                                    for l in lines:
                                      with settings(warn_only=True):
                                        if run ( "sed -n '/SF:.*" + filename[-1] + "/,/end_of_record/p' base.info |grep DA:" + l):
                                          self.uncovered_lines += 1
                                          self.uncovered_lines_list[-1].append(l)
                              else:
                                print 'No file found ' + f + '\n'
                # save results
                if self.covered_lines > 0:
                    self.average = round( ((self.covered_lines / (self.covered_lines +
                                                                  self.uncovered_lines)) 
                                           * 100), 2)
                self.count_hunks(prev_revision)

    def prev_patch_coverage(self, backcnt, prev_files, prev_lines):
        assert len(prev_files) == len(prev_lines)
        
        prev_files_same = []
        prev_lines_same = []
        for i, f in enumerate(prev_files):
            if f not in self.changed_files:
                prev_files_same.append(f)
                prev_lines_same.append(prev_lines[i])
        
        """ ignore files that are modified """
        prev_files = prev_files_same;
        prev_lines = prev_lines_same;
        if self.compileError:
          return (prev_files, prev_lines)

        covered = 0
        for i, f in enumerate(prev_files):
            covered += len(prev_lines[i])
            prev_lines[i][:] = [ l for l in prev_lines[i] if self.is_covered(f, l) != self.LineType.Covered ]
            covered -= len(prev_lines[i])

        assert(len(self.prev_covered) >= backcnt)
        if (len(self.prev_covered) == backcnt):
          self.prev_covered.append(covered)
        else:
          self.prev_covered[backcnt] += covered;
        return (prev_files, prev_lines)
                
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
        c.merge = self.merge
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
                c.summary = run('cat ' + self.source_path + '/coverage.txt')
            c.compileError = self.compileError
            c.maketestError = self.maketestError
            c.prev_covered  = self.prev_covered
            c.hunks = len(self.hunkheads)
            c.ehunks = len(self.ehunkheads)
            c.hunks3 = len(self.hunkheads3)
            c.ehunks3 = len(self.ehunkheads3)
            c.changed_files = len(self.changed_files)
            c.echanged_files = len(self.echanged_files)
            c.changed_test_files = len(self.changed_test_files)

        # pass the Collector() obj to the Data Handler to store results in CSV format
        x = DataHandler(c)
        x.extractData()
        x.dumpCSV()
        print "Files modified in the revision: " + str(self.changed_files) + '\n'
        print "Lines modified and uncovered in the revision: " + str(self.uncovered_lines_list) + '\n'
