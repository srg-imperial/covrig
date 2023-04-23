import subprocess
import sys

from fabric import Connection
import docker
import fnmatch
import random
import time

# Analytics modules
from DataHandler import *


class EmptyContextManager:
    def __enter__(self):
        return

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

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

        # connection_attempts no longer supported

        if self.offline:
            self.initialpath = self.local("realpath .").stdout.strip()
            self.difflinessh = "%s/deps/measure-cov.sh" % self.initialpath
        else:
            self.difflinessh = "/root/measure-cov.sh"

    # The following are methods used to spawn a new container
    #

    def sshd_up(self):
        """ set up sshd """
        print(self.image)
        # Pick a random number between 60001 and 61000 for the port mapping, and try to create a container, retry if the port is already in use
        # Do this 20 times (arbitrary number) before giving up, and wait a random amount of time between retries
        attempts, max_retries = 0, 20
        random_port = -1
        while attempts < max_retries:
            # This is a hack to get around the fact that the port is already allocated
            random_port = random.randint(60001, 60999)
            try:
                self.container = self.client.containers.create(self.image,
                                                               command='/usr/sbin/sshd -D',
                                                               ports={22: random_port})
                self.cnt_id = self.container.id
                self.container.start() # This line is the one that fails if the port is already allocated
                break
            except Exception as e:
                print(f"Docker threw error: {e}")
                print(f"Most likely port {random_port} already allocated, retrying...")
                time.sleep(random.uniform(0.1, 1))
                attempts += 1
        if attempts == max_retries:
            print("Could not create container, giving up")
            sys.exit(1)
        print(f"Started container {self.cnt_id[:8]} on port {random_port}")

    def set_ip(self):
        """ set container ID """
        # state = self.client.inspect_container(self.cnt_id)
        state = self.client.containers.get(self.cnt_id).attrs
        self.ip = state['NetworkSettings']['IPAddress']
        print(f"Assigned container {self.cnt_id[:8]} IP {self.ip}")

    def fabric_setup(self):
        #     """ set fabric env parameters """
        #     env.user = self.user
        #     env.password = self.pwd
        #     env.host_string = self.ip + ':22'
        #     # in a perfect world, this would not be here
        #     env.connection_attempts = 10
        self.try_to_connect()

    def try_to_connect(self, max_connection_attempts=10):
        # Get the ubuntu version from the image, so we can use the correct sshd_config
        labels = self.client.images.get(self.image).attrs['Config']['Labels']
        if labels is None or 'ubuntu_version' not in labels:
            image_version = 14.04
            print('LABEL "ubuntu_version" not found in image, assuming <= 14.04')
        else:
            image_version = float(labels['ubuntu_version'])

        tries = 0
        # Do this 10 times (arbitrary number) before giving up, use backoff
        while tries < max_connection_attempts:
            try:
                # if the image is ubuntu 14.04 or prior, use the old sshd_config
                if image_version < 16:
                    self.conn = Connection(host=self.ip, port=22, user=self.user,
                                           connect_kwargs={
                                               "disabled_algorithms": {"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]}
                                           })
                else:
                    self.conn = Connection(host=self.ip, port=22, user=self.user)
                return
            except Exception as e:
                print(f'Failed to connect to container: {e}')
                tries += 1
                if tries < max_connection_attempts:
                    print(f'Retrying... ({tries})')
                    time.sleep((1.5 ** tries)/3) # exponential backoff scale to 12s
        print(f'Error: Maximum number of connection attempts exceeded.')

    def try_to_run(self, cmd, max_connection_attempts=10, **kwargs):
        tries = 0
        while tries < max_connection_attempts:
            try:
                run = self.conn.run(cmd, **kwargs)
                return run
            except Exception as e:
                print(f'Failed to run on container: {e}')
                tries += 1
                if tries < max_connection_attempts:
                    print(f'Retrying... ({tries})')
                    time.sleep((1.5 ** tries) / 3)  # exponential backoff scale to 12s
        print(f'Error: Maximum number of run attempts exceeded.')
        return None

    def run_test(self):
        """ uname to check everything works """
        self.conn.run('uname -on')

    def local(self, cmd: str, text=True, **kwargs):
        return subprocess.run([cmd], shell=True, capture_output=True, text=text, **kwargs)

    def omnicd(self, path):
        if self.offline:
            # TODO: lcd no longer supported so just use cd for now?
            # or use a local('cd ...')
            # if hasattr(self, "conn") and self.conn:
            #     return self.conn.lcd(path)
            return EmptyContextManager()
        else:
            return self.conn.cd(path)

    def omnirun(self, cmd, **kwargs):
        print("running %s" % cmd)
        if self.offline:
            # return self.conn.local(cmd, capture=True, **kwargs)
            kwargs.pop('warn', None)
            text = kwargs.pop('text', True)  # Capture text arg if it can be found, otherwise True.
            return self.local(cmd, text=text, **kwargs)
        else:
            kwargs.pop('cwd', None)  # Cleanse of cwd magic for a standard fabric run
            kwargs.pop('text', None)
            return self.try_to_run(cmd, **kwargs)
            # return self.conn.run(cmd, **kwargs)

    def spawn(self):
        if not self.offline:
            """ call all the methods needed to spawn a container """
            self.sshd_up()
            self.set_ip()
            self.fabric_setup()

    def halt(self, max_connection_attempts=10):
        if not self.offline:
            """ shutdown the current container """
            print('\n\nHalting the current container...\n\n')
            tries = 0
            while tries < max_connection_attempts:
                try:
                    self.conn.close()
                    self.container.stop()
                    self.container.remove(force=True)
                    return
                except Exception as e:
                    print(f'Failed to stop container: {e}')
                    tries += 1
                    if tries < max_connection_attempts:
                        print(f'Retrying... ({tries})')
                        time.sleep((1.5 ** tries) / 3)
            print(f'Error: Maximum number of stop attempts exceeded.')

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
                lines += int(self.omnirun("cloc " + p + " | tail -2 | awk '{print $5}'").stdout.strip())
            except ValueError:
                lines += int(self.omnirun("wc -l " + p + "/*|tail -1|awk '{ print $1 }'").stdout.strip())
        return str(lines)

    def count_hunks(self, prev_revision):
        cwd = None
        if self.offline:
            cwd = self.path
        with self.omnicd(self.path):
            changed = self.omnirun("git diff -b -U0 " +
                                   prev_revision + " " + self.revision +
                                   " | perl -pe 's/\e\[?.*?[\@-~]//g'", cwd=cwd, text=False)
            # Make sure not in text mode as can be passed illegal utf8 encoded characters
            if changed:
                changed_stripped = changed.stdout.splitlines()
                if self.offline:
                    self.hunkheads = [i for i in changed_stripped if i.decode('utf-8', 'replace').startswith('@@')]
                else:
                    self.hunkheads = [i for i in changed_stripped if i.startswith('@@')]
                changed = self.omnirun("git diff -b " +
                                       prev_revision + " " + self.revision +
                                       " | perl -pe 's/\e\[?.*?[\@-~]//g'", cwd=cwd, text=False)
                changed_stripped = changed.stdout.splitlines()
                if self.offline:
                    self.hunkheads3 = [i for i in changed_stripped if i.decode('utf-8', 'replace').startswith('@@')]
                else:
                    self.hunkheads3 = [i for i in changed_stripped if i.startswith('@@')]

    def checkout(self, prev_revision, revision):
        """ checkout the revision we want """
        # set the revision for current execution (commit sha)
        self.revision = revision
        cwd = None
        if self.offline:
            cwd = self.path
        with self.omnicd(self.path):
            print('path is ' + self.path)
            self.omnirun('git checkout ' + revision, cwd=cwd)
            self.is_merge(revision)
            diffcmd = "git diff -b --pretty='format:' --name-only " + prev_revision + " " + self.revision + " -- "
            if hasattr(self, 'limit_changes_to'):
                for path in self.limit_changes_to:
                    diffcmd += path + " "
            diffcmd += " | perl -pe 's/\e\[?.*?[\@-~]//g'"
            result = self.omnirun(diffcmd, cwd=cwd)
            if result.stdout.strip() == "":
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
            # Don't warn=True - we need this to work
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
                res = self.local('rm -rf tmp && mkdir tmp && tar xjf coverage-%s.tar.bz2 -C tmp' % self.revision, cwd=covdatadir)
                if res.returncode != 0:
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

        cwd = None
        if self.offline:
            cwd = covdatadir
        with self.omnicd(covdatadir):
            ignore = ' '.join(["'%s'" % p for p in self.tsuite_path])
            self.omnirun('lcov --rc lcov_branch_coverage=1 -r total.info %s -o total.info' % ignore, warn=True, cwd=cwd)
            if hasattr(self, 'ignore_coverage_from'):
                ignore = ' '.join(["'%s'" % p for p in self.ignore_coverage_from])
                self.omnirun('lcov --rc lcov_branch_coverage=1 -r total.info %s -o total.info' % ignore, warn=True, cwd=cwd)
            lines = self.omnirun(
                "lcov --rc lcov_branch_coverage=1 --summary total.info 2>&1|tail -3|head -1|sed 's/.*(//' |egrep -o '[0-9]+'",
                warn=True, cwd=cwd)
            lines = lines.stdout.splitlines()
            if len(lines) == 2:
                self.covered_eloc = lines[0]
                self.total_eloc = lines[1]

            branches = self.omnirun(
                "lcov --rc lcov_branch_coverage=1 --summary total.info 2>&1|tail -1|sed 's/.*(//' |egrep -o '[0-9]+'",
                warn=True, cwd=cwd)
            branches = branches.stdout.splitlines()
            if len(branches) == 2:
                self.covered_branches = branches[0]
                self.total_branches = branches[1]

    def has_coverage_information(self, filepath):
        cwd = None
        if self.offline:
            covdatadir = '%s/data/%s/tmp' % (self.initialpath, self.outputfolder)
            cwd = covdatadir
        else:
            covdatadir = self.source_path

        print(covdatadir)
        with self.omnicd(covdatadir):
            result = self.omnirun("sed -n '\|SF:.*/%s|,/end_of_record/p' total.info" % filepath, cwd=cwd)
        return bool(result.stdout.strip())

    def is_covered(self, filepath, line):
        cwd = None
        if self.offline:
            covdatadir = '%s/data/%s/tmp' % (self.initialpath, self.outputfolder)
            cwd = covdatadir
        else:
            covdatadir = self.source_path

        with self.omnicd(covdatadir):
            result = self.omnirun("sed -n '\|SF:.*/%s|,/end_of_record/p' total.info |grep '^DA:%d,'" % (filepath, line),
                                  warn=True, cwd=cwd)
            if (hasattr(result, 'ok') and not result.ok) or (hasattr(result, 'returncode') and result.returncode != 0):
                return self.LineType.NotExecutable
            elif result.stdout.strip().endswith(",0"):
                return self.LineType.NotCovered
            else:
                return self.LineType.Covered

    def is_merge(self, commit):
        cwd = None
        if self.offline:
            cwd = self.path
        with self.omnicd(self.path):
            mergestatus = self.omnirun("git show " + commit + "|head -2|tail -1", cwd=cwd)
            self.merge = mergestatus.stdout.strip().startswith("Merge:")
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
        cwd = None
        if self.offline:
            cwd = self.path
        with self.omnicd(self.path):
            diffcmd = "git diff -b --pretty='format:' --name-only " + prev_revision + " " + self.revision + " -- "
            if hasattr(self, 'limit_changes_to'):
                for path in self.limit_changes_to:
                    diffcmd += path + " "
            diffcmd += " | perl -pe 's/\e\[?.*?[\@-~]//g'"

            changed_files = self.omnirun(diffcmd, cwd=cwd)
            if changed_files.stdout:
                self.changed_files = [i for i in changed_files.stdout.splitlines() if i]
                print(self.changed_files)
                # for every changed file 
                for f in self.changed_files:
                    # get the filename
                    self.uncovered_lines_list.append([])
                    if not self.compileError:
                        # check whether it's a test file
                        # with self.omnicd(self.path): #TODO: aren't we already in context? I'm commenting of this
                        fileExists = self.omnirun('[ -f ' + f + ' ] && echo y || echo n', cwd=cwd)
                        if fileExists.stdout.strip() == 'y':
                            realp = self.omnirun('realpath ' + f, cwd=cwd).stdout.strip()
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
                            # with self.omnicd(self.path):
                            file_diff = self.omnirun("git diff -b -U0 " +
                                                     prev_revision + " " + self.revision +
                                                     " -- " + f +
                                                     " | perl -pe 's/\e\[?.*?[\@-~]//g'", cwd=cwd)
                            self.ehunkheads += [i for i in file_diff.stdout.splitlines() if i.startswith('@@')]
                            file_diff3 = self.omnirun("git diff -b " +
                                                      prev_revision + " " + self.revision +
                                                      " -- " + f +
                                                      " | perl -pe 's/\e\[?.*?[\@-~]//g'", cwd=cwd)
                            self.ehunkheads3 += [i for i in file_diff3.stdout.splitlines() if i.startswith('@@')]
                            line_numbers = self.omnirun(
                                "%s %s %s %s" % (self.difflinessh, prev_revision, self.revision, f), cwd=cwd)
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

                            # with self.omnicd(self.path):
                            fileExists = self.omnirun('[ -f ' + f + ' ] && echo y || echo n', cwd=cwd)
                            if fileExists.stdout.strip() == 'y':
                                line_numbers = self.omnirun(
                                    "%s %s %s %s" % (self.difflinessh, prev_revision, self.revision, f), cwd=cwd)
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
