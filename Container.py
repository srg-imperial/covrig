from __future__ import division
from fabric import Connection
import docker
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
        self.container = None
        self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')

        self.image = _image
        self.user = _user
        self.pwd = _pwd

        self.offline = not _image
        # no errors yet :)
        self.compileError = False
        self.maketestError = False
        self.emptyCommit = False
        """ how many lines from previous patches are covered now """
        self.changed_files = []
        self.echanged_files = []
        self.uncovered_lines_list = []
        self.prev_covered = []
        self.hunkheads = []
        self.ehunkheads = []
        self.hunkheads3 = []
        self.ehunkheads3 = []

        self.tsize = 0
        # split the test suite into directories and files
        self.tsuite_dir = []
        self.tsuite_file = []

        self.changed_test_files = []
        self.merge = False
        self.total_eloc = 0
        self.covered_eloc = 0
        self.total_branches = 0
        self.covered_branches = 0

        self._gcovNameCache = set()
        self._gcovNoNameCache = set()

        # self.conn = Connection(user=self.user, host="", port=22, connect_kwargs={"pwd": self.pwd}) # TODO: host gets set later
        # connection_attempts no longer supported

        if self.offline:
            # self.initialpath = self.conn.local("realpath .", capture=True) # TODO: how could this have been called if fabric_setup hadn't been called yet?
            self.difflinessh = "%s/deps/measure-cov.sh" % self.initialpath
        else:
            self.difflinessh = "/root/measure-cov.sh"

    # The following are methods used to spawn a new container
    #

    def sshd_up(self):
        """ set up sshd """
        print(self.image)
        self.container = self.client.containers.create(self.image,
                                                       command='/usr/sbin/sshd -D',
                                                       ports={22: 60002})
        self.cnt_id = self.container.id
        self.container.start()
        # TODO: doesn't autocomplete, hopefully this is right

    def set_ip(self):
        """ set container ID """
        # state = self.client.inspect_container(self.cnt_id)
        state = self.client.containers.get(self.cnt_id).attrs
        self.ip = state['NetworkSettings']['IPAddress']

    def fabric_setup(self):
        #     """ set fabric env parameters """
        #     env.user = self.user
        #     env.password = self.pwd
        #     env.host_string = self.ip + ':22'
        #     # in a perfect world, this would not be here
        #     env.connection_attempts = 10
        # self.conn = Connection(user=self.user, host=self.ip, port=22, connect_kwargs={"password": self.pwd, "passphrase": "project", "look_for_keys": False, "allow_agent": False})
        # self.conn = Connection(user=self.user, host=self.ip, port=22,
        #                        connect_kwargs={"password": self.pwd})
        # TODO: Password seems to be the passphrase for the private key I set up instead?
        # self.conn = Connection(host=self.ip, port=22, connect_kwargs={"password": "project"})
        self.conn = Connection(host=self.ip, port=22, user=self.user)

    def run_test(self):
        """ uname to check everything works """
        self.conn.run('uname -on')

    def omnicd(self, path):
        if self.offline:
            # TODO: lcd no longer supported so just use cd for now?
            # or use a local('cd ...')
            return self.conn.lcd(path)
        else:
            return self.conn.cd(path)

    def omnirun(self, cmd, **kwargs):
        print("running %s" % cmd)
        if self.offline:
            return self.conn.local(cmd, capture=True, **kwargs)
        else:
            return self.conn.run(cmd, **kwargs)

    def spawn(self):
        if not self.offline:
            """ call all the methods needed to spawn a container """
            self.sshd_up()
            self.set_ip()
            self.fabric_setup()

    def halt(self):
        if not self.offline:
            """ shutdown the current container """
            print('\n\nHalting the current container...\n\n')
            self.container.stop()
            self.container.remove()

    def get_commits(self, n, ending_at=''):
        """ attach timestamp and author to a given commit """
        commitlist = self.omnirun(
            'cd %s && git rev-list -n %d --first-parent --format=%%h__%%ct__%%an %s|grep -v commit' % (
                self.path, n, ending_at))
        return commitlist.stdout.splitlines()

    def count_sloc(self, path):
        """ use cloc to get the static lines of code for any given file or directory """
        lines = 0
        for p in path:
            try:
                lines += int(self.omnirun("cloc " + p + " | tail -2 | awk '{print $5}'").stdout)
            except ValueError:
                lines += int(self.omnirun("wc -l " + p + "/*|tail -1|awk '{ print $1 }'").stdout)
        return str(lines)

    def count_hunks(self, prev_revision):
        with self.omnicd(self.path):
            changed = self.omnirun("git diff -b -U0 " +
                                   prev_revision + " " + self.revision +
                                   " | perl -pe 's/\e\[?.*?[\@-~]//g'")
            if changed:
                self.hunkheads = [i for i in changed.stdout.splitlines() if i.startswith('@@')]
                changed = self.omnirun("git diff -b " +
                                       prev_revision + " " + self.revision +
                                       " | perl -pe 's/\e\[?.*?[\@-~]//g'")
                self.hunkheads3 = [i for i in changed.stdout.splitlines() if i.startswith('@@')]

    def checkout(self, prev_revision, revision):
        """ checkout the revision we want """
        # set the revision for current execution (commit sha)
        self.revision = revision
        with self.omnicd(self.path):
            print('path is ' + self.path)
            result = self.omnirun('git checkout ' + revision)
            self.is_merge(revision)
            diffcmd = "git diff -b --pretty='format:' --name-only " + prev_revision + " " + self.revision + " -- "
            if hasattr(self, 'limit_changes_to'):
                for path in self.limit_changes_to:
                    diffcmd += path + " "
            diffcmd += " | perl -pe 's/\e\[?.*?[\@-~]//g'"
            result = self.omnirun(diffcmd)
            if not result:
                self.emptyCommit = True

    def tsize_compute(self):
        """ compute test suite as SLOCs """
        # rebuild the test suite with only files or dirs that 
        # actually exists in the current revision
        actual_tsuite = []
        for item in self.tsuite_path:
            item = "%s/%s" % (self.path, item)
            fileExists = self.omnirun('ls -U ' + item + ' >/dev/null 2>&1 && echo y || echo n')
            if fileExists.stdout.strip() == 'y':
                actual_tsuite.append(item)
                print('Added ' + item + ' to the test suite\n')
                isdir = self.omnirun('[ -d "' + item + '" ] && echo y || echo n')
                if isdir.stdout.strip() == 'y':
                    self.tsuite_dir.append(item)
                else:
                    self.tsuite_file.append(item)
        self.tsuite_path = actual_tsuite
        # XXX count_sloc will fail if a wildcard path contains no files recognized by cloc
        self.tsize = self.count_sloc(self.tsuite_path)

    def backup(self, commit):
        assert not self.offline

        """ create a tar.bz2 with .gcov and lcov .info files and save it to localhost """
        if self.compileError or self.emptyCommit:
            return
        with self.omnicd(self.source_path):
            # save gcov/gcc/g++ info
            self.conn.run('gcov -v | head -1 > build_info.txt', warn=True)
            self.conn.run('echo >> build_info.txt', warn=True)
            self.conn.run('gcc -v &>> build_info.txt', warn=True)
        with self.omnicd(self.source_path):
            # bzip all the coverage files
            self.conn.run("find . -name '*.gcov' -or -name '*.info' > backuplist")
            self.conn.run("echo ./build_info.txt >> backuplist")
            self.conn.run('tar -cjf coverage-' + commit + '.tar.bz2 -T backuplist')
            # scp to localhost/data
            self.conn.get(self.source_path + '/coverage-' + commit + '.tar.bz2', local='data/' + self.outputfolder +
                          '/' + 'coverage-' + commit + '.tar.bz2')

    def rec_initial_coverage(self):
        assert not self.offline
        with self.omnicd(self.source_path):
            self.conn.run('lcov --rc lcov_branch_coverage=1 -c -i -d . -o base.info')

    def make_test(self):
        assert not self.offline
        if self.compileError or self.emptyCommit:
            return
        self.rec_initial_coverage()

    def overall_coverage(self):
        """ collect overall coverage results """
        if self.compileError or self.emptyCommit:
            return

        if self.offline:
            covdatadir = '%s/data/%s' % (self.initialpath, self.outputfolder)
            with self.omnicd(covdatadir):
                res = self.conn.local('rm -rf tmp && mkdir tmp && tar xjf coverage-%s.tar.bz2 -C tmp' % self.revision,
                                      warn=True)
                if res.failed:
                    return
                covdatadir += "/tmp"
        else:
            covdatadir = self.source_path
            with self.omnicd(covdatadir):
                res = self.omnirun('lcov --rc lcov_branch_coverage=1 -c -d . -o test.info', warn=True)
                if res.failed:
                    return
                self.conn.run("lcov --rc lcov_branch_coverage=1 -a base.info -a test.info -o total.info", warn=True)
                self.conn.run('find -name "*.gcda"|xargs gcov', hide=True, warn=True)  # From quiet to hide

        with self.omnicd(covdatadir):
            ignore = ' '.join(["'%s'" % p for p in self.tsuite_path])
            self.omnirun('lcov --rc lcov_branch_coverage=1 -r total.info %s -o total.info' % ignore, warn=True)
            if hasattr(self, 'ignore_coverage_from'):
                ignore = ' '.join(["'%s'" % p for p in self.ignore_coverage_from])
                self.omnirun('lcov --rc lcov_branch_coverage=1 -r total.info %s -o total.info' % ignore, warn=True)
            lines = self.omnirun(
                "lcov --rc lcov_branch_coverage=1 --summary total.info 2>&1|tail -3|head -1|sed 's/.*(//' |egrep -o '[0-9]+'",
                warn=True)
            lines = lines.stdout.splitlines()
            if len(lines) == 2:
                self.covered_eloc = lines[0]
                self.total_eloc = lines[1]

            branches = self.omnirun(
                "lcov --rc lcov_branch_coverage=1 --summary total.info 2>&1|tail -1|sed 's/.*(//' |egrep -o '[0-9]+'",
                warn=True)
            branches = branches.stdout.splitlines()
            if len(branches) == 2:
                self.covered_branches = branches[0]
                self.total_branches = branches[1]

    def has_coverage_information(self, filepath):
        if self.offline:
            covdatadir = '%s/data/%s/tmp' % (self.initialpath, self.outputfolder)
        else:
            covdatadir = self.source_path

        print(covdatadir)
        with self.omnicd(covdatadir):
            result = self.omnirun("sed -n '\|SF:.*/%s|,/end_of_record/p' total.info" % filepath)
        return bool(result.stdout)

    def is_covered(self, filepath, line):
        if self.offline:
            covdatadir = '%s/data/%s/tmp' % (self.initialpath, self.outputfolder)
        else:
            covdatadir = self.source_path

        with self.omnicd(covdatadir):
            result = self.omnirun("sed -n '\|SF:.*/%s|,/end_of_record/p' total.info |grep '^DA:%d,'" % (filepath, line),
                                  warn=True)
            if result.ok:
                return self.LineType.NotExecutable
            elif result.stdout.endswith(",0"):
                return self.LineType.NotCovered
            else:
                return self.LineType.Covered

    def is_merge(self, commit):
        with self.omnicd(self.path):
            mergestatus = self.omnirun("git show " + commit + "|head -2|tail -1")
            self.merge = mergestatus.stdout.startswith("Merge:")
            return self.merge

    def patch_coverage(self, prev_revision):
        """ compute the coverage for the current commit """
        self.added_lines = 0
        self.covered_lines = 0
        self.uncovered_lines = 0
        self.average = 0

        if self.compileError or self.emptyCommit or self.covered_eloc == 0:
            return
        # get a list of the changed files for the current commit
        with self.omnicd(self.path):
            diffcmd = "git diff -b --pretty='format:' --name-only " + prev_revision + " " + self.revision + " -- ";
            if hasattr(self, 'limit_changes_to'):
                for path in self.limit_changes_to:
                    diffcmd += path + " "
            diffcmd += " | perl -pe 's/\e\[?.*?[\@-~]//g'"

            changed_files = self.omnirun(diffcmd)
            if changed_files.stdout:
                self.changed_files = [i for i in changed_files.stdout.splitlines() if i]
                print(self.changed_files)
                # for every changed file 
                for f in self.changed_files:
                    # get the filename
                    self.uncovered_lines_list.append([])
                    if not self.compileError:
                        # check whether it's a test file
                        with self.omnicd(self.path):
                            fileExists = self.omnirun('[ -f ' + f + ' ] && echo y || echo n')
                            if fileExists.stdout.strip() == 'y':
                                realp = self.omnirun('realpath ' + f).stdout
                                for tf in self.tsuite_file:
                                    if fnmatch.fnmatch(realp, tf):
                                        self.changed_test_files.append(f)
                                for td in self.tsuite_dir:
                                    if realp.startswith(td + "/"):
                                        self.changed_test_files.append(f)
                        self.changed_test_files = list(set(self.changed_test_files))
                        if self.has_coverage_information(f):
                            print('Coverage information found\n')
                            self.echanged_files.append(f)
                            # get the changed lines numbers
                            with self.omnicd(self.path):
                                file_diff = self.omnirun("git diff -b -U0 " +
                                                         prev_revision + " " + self.revision +
                                                         " -- " + f +
                                                         " | perl -pe 's/\e\[?.*?[\@-~]//g'")
                                self.ehunkheads += [i for i in file_diff.stdout.splitlines() if i.startswith('@@')]
                                file_diff3 = self.omnirun("git diff -b " +
                                                          prev_revision + " " + self.revision +
                                                          " -- " + f +
                                                          " | perl -pe 's/\e\[?.*?[\@-~]//g'")
                                self.ehunkheads3 += [i for i in file_diff3.stdout.splitlines() if i.startswith('@@')]
                            line_numbers = self.omnirun(
                                "%s %s %s %s" % (self.difflinessh, prev_revision, self.revision, f))
                            # for every changed line
                            for l in line_numbers.stdout.splitlines():
                                # increment added lines
                                self.added_lines += 1
                                covstatus = self.is_covered(f, int(l))
                                if covstatus == self.LineType.NotCovered:
                                    self.uncovered_lines += 1
                                    self.uncovered_lines_list[-1].append(int(l))
                                elif covstatus == self.LineType.Covered:
                                    self.covered_lines += 1
                        else:
                            # no coverage information found
                            # most likely the file was not compiled into any of the programs
                            # executed by the test suite. Alternatives include: file was removed, program crashed or has no permissions
                            print('No coverage information found for ' + f + '\n')

                            with self.omnicd(self.path):
                                fileExists = self.omnirun('[ -f ' + f + ' ] && echo y || echo n')
                                if fileExists.stdout.strip() == 'y':
                                    line_numbers = self.omnirun(
                                        "%s %s %s %s" % (self.difflinessh, prev_revision, self.revision, f))
                                    lines = line_numbers.stdout.splitlines()
                                    self.added_lines += len(lines)
                                else:
                                    print('No file found ' + f + '\n')
                # save results
                if self.covered_lines > 0:
                    self.average = round(((self.covered_lines / (self.covered_lines +
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
        prev_files = prev_files_same
        prev_lines = prev_lines_same
        if self.compileError or self.emptyCommit or self.covered_eloc == 0:
            return prev_files, prev_lines

        covered = 0
        for i, f in enumerate(prev_files):
            covered += len(prev_lines[i])
            prev_lines[i][:] = [l for l in prev_lines[i] if self.is_covered(f, l) != self.LineType.Covered]
            covered -= len(prev_lines[i])

        assert (len(self.prev_covered) >= backcnt)
        if len(self.prev_covered) == backcnt:
            self.prev_covered.append(covered)
        else:
            self.prev_covered[backcnt] += covered
        return prev_files, prev_lines

    def collect(self, author_name, timestamp, outputfolder, outputfile):
        """ create a Collector to collect all info and a XMLHandler to parse them """
        c = Collector()
        # the class name which is actually running this method, as a string
        c.name = self.__class__.__name__
        c.outputfile = outputfile
        c.outputfolder = outputfolder
        # fill in some info about the test
        c.revision = self.revision
        c.author_name = author_name
        c.timestamp = timestamp
        c.tsuite_size = self.tsize
        c.merge = self.merge
        # if compilation failed, halt
        if self.compileError:
            c.compileError = True
        # go on
        elif self.emptyCommit:
            c.emptyCommit = True
        else:
            # fill patch coverage results
            c.added_lines = self.added_lines
            c.covered_lines = self.covered_lines
            c.uncovered_lines = self.uncovered_lines
            c.average = self.average
            # fill overall coverage results and exit status
            c.covered_eloc = self.covered_eloc
            c.total_eloc = self.total_eloc
            c.covered_branches = self.covered_branches
            c.total_branches = self.total_branches
            c.compileError = self.compileError
            c.maketestError = self.maketestError
            if self.covered_eloc:
                c.prev_covered = self.prev_covered
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
        print("Files modified in the revision: " + str(self.changed_files) + '\n')
        print("Lines modified and uncovered in the revision: " + str(self.uncovered_lines_list) + '\n')
