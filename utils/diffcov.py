# Python implementation of the diffcov.sh script

import argparse
import shutil
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor


def log_popen_pipe(p, stdfile, filename=None):
    with open(filename, "w") as f:

        while p.poll() is None:
            f.write(stdfile.readline())
            f.flush()

        # Write the rest from the buffer
        f.write(stdfile.read())

def run(cmd: str | list[str], text=True, **kwargs):
    # Extract an error_msg from the kwargs
    error_msg = kwargs.pop("error_msg", None)
    # Extract a show_output from the kwargs
    show_output = kwargs.pop("show_output", False)
    # Extract a as_list from the kwargs
    as_list = kwargs.pop("as_list", False)
    if as_list:
        result = subprocess.run(cmd, shell=False, text=text, **kwargs)
    else:
        result = subprocess.run([cmd], shell=True, capture_output=True, text=text, **kwargs)
    if result.returncode != 0:
        if error_msg:
            print(error_msg)
            if show_output:
                print(result.stdout)
                print(result.stderr)
        else:
            print(f"Failed to run {cmd}.")
        sys.exit(1)
    return result


def build_repo_snapshot(repo: str, archive: str, revision: str, name: str, source: str = "", ignore: str = ""):
    # Git checkout the repo at the specified revision (repos/<repo>)
    run(f"git -C repos/{repo} checkout {revision}", error_msg=f"Failed to checkout {revision} of {repo}.")

    # Copy the code at that revision in repos/<repo> to the specified directory (diffcov/<name>)
    run(f"cp -r repos/{repo}/* diffcov/{name}", error_msg=f"Failed to copy {repo} to diffcov/{name}.")

    # Create a temporary directory (diffcov/<name>.tmp)
    run(f"mkdir -p diffcov/{name}.tmp", error_msg=f"Failed to create diffcov/{name}.tmp.")

    # Copy the coverage archive to the temporary directory (diffcov/<name>.tmp)
    run(f"cp {archive}/coverage-{revision}.tar.bz2 diffcov/{name}.tmp",
        error_msg=f"Failed to copy coverage-{revision}.tar.bz2 to diffcov/{name}.tmp.")

    # Extract the coverage archive in the temporary directory (diffcov/<name>.tmp)
    run(f"tar -xjf diffcov/{name}.tmp/coverage-{revision}.tar.bz2 -C diffcov/{name}.tmp",
        error_msg=f"Failed to extract {revision}.tar.bz2 in diffcov/{name}.tmp.")

    # Remove the coverage archive from the temporary directory (diffcov/<name>.tmp)
    run(f"rm diffcov/{name}.tmp/coverage-{revision}.tar.bz2",
        error_msg=f"Failed to remove coverage-{revision}.tar.bz2 from diffcov/{name}.tmp.")

    # Find the locations of all of the sources of the gcov files in the temporary directory (diffcov/<name>.tmp)
    # Get the names of all of the gcov files in the temporary directory (diffcov/<name>.tmp)
    result = run(f"find diffcov/{name}.tmp -name '*.gcov'",
                 error_msg=f"Failed to find all of the gcov files in diffcov/{name}.tmp.")
    if result.stdout.strip() == "":
        print(f"No gcov files found in diffcov/{name}.tmp.")
        sys.exit(1)
    gcov_files = result.stdout.splitlines()

    # Strip the .gcov extension from the gcov files
    gcov_files_stripped = [gcov_file[:-5] for gcov_file in gcov_files]

    # For each gcov file, find the corresponding source file in diffcov/<name>
    source_file_list = []
    source_file_git_list = []
    for gcov_file, gcov_file_stripped in zip(gcov_files, gcov_files_stripped):
        # Only keep the base name of the gcov files
        gcov_file_base = os.path.basename(gcov_file_stripped)

        # Get the name of the source file
        result = run(f"find diffcov/{name} -name '{gcov_file_base}'",
                     error_msg=f"Failed to find the source file for {gcov_file} (looking for {gcov_file_base}.")

        source_file = ""
        if result.stdout.strip() == "":
            print(f"Could not find the source file for {gcov_file} (looking for {gcov_file_base}).")

        combined_results = result.stdout.splitlines()
        # Filter out any results that include the ignore string
        if ignore:
            combined_results = [x for x in combined_results if ignore not in x]
        # If there are no results left, throw a warning
        if len(combined_results) == 0:
            print(f"Could not find the source file for {gcov_file} (looking for {gcov_file_base}).")

        if len(combined_results) > 1:
            # If result returns multiple lines analyse total.info for the correct path
            # Create a list of matching source files
            matching_source_files = combined_results
            # Extract the path to the source file from total.info
            result = run(f"grep '{gcov_file_base}' diffcov/{name}.tmp/total.info",
                         error_msg=f"Failed to extract the path to the source file from total.info.")
            # Throw a warning if multiple lines are returned
            if len(result.stdout.splitlines()) > 1:
                print(f"Found multiple lines in total.info for {gcov_file_base}, taking the first.")
                result = result.stdout.splitlines()[0]
            sf = result.stdout.strip()[3:]
            # Return sf with everything beyond and not including <repo>
            source_file = sf[sf.find(repo) + len(repo) + 1:]
            # Prepend the path to the source file with diffcov/<name>
            source_file = f"diffcov/{name}/{source_file}"

            # As an extra check, check that the source file is in the list of matching source files
            if os.path.basename(source_file) not in [os.path.basename(x) for x in matching_source_files]:
                print(f"Could not find the source file for {gcov_file} (looking for {gcov_file_base}).")
                sys.exit(1)

            # Get the first non-empty line of the source file
            result = run(f"grep -m 1 -v '^$' {source_file}",
                         error_msg=f"Failed to find the first non-empty line of {source_file}.")
            # Assert that we can find this in the gcov file
            result = run(f"grep -q '{result.stdout.strip()}' {gcov_file}",
                         error_msg=f"Failed to find the first non-empty line of {source_file} in {gcov_file}.")
        else:
            source_file = combined_results[0]

        # Add the source file to the list of source files
        source_file_list.append(source_file)

        # Get the directory of the source file
        source_file_dir = os.path.dirname(source_file)

        # Copy the gcov file to the directory of the source file
        run(f"cp {gcov_file} {source_file_dir}", error_msg=f"Failed to copy {gcov_file} to {source_file_dir}.")

        # Find the corresponding file with in the git repo
        # Cut off the diffcov/<name> part of the source file
        source_file_git = source_file[source_file.find(f"diffcov/{name}") + len(f"diffcov/{name}") + 1:]
        # Prepend the path to the git repo
        source_file_git = f"{repo}/{source_file_git}"
        # Add the source file to the list of source files
        source_file_git_list.append(source_file_git)

    # If a source directory is specified, copy all the .info files in the top level of the temporary directory (diffcov/<name>.tmp) to the source directory
    # Otherwise they will be copied to diffcov/<name>
    run(f"cp diffcov/{name}.tmp/*.info diffcov/{name}/{source}", error_msg=f"Failed to copy *.info files to {source}")

    # Remove the temporary directory (diffcov/<name>.tmp)
    run(f"rm -rf diffcov/{name}.tmp", error_msg=f"Failed to remove diffcov/{name}.tmp.")

    # Print a message to say that the coverage archive has been extracted
    print(f"Extracted coverage archive for {revision} ('{name}') and merged with sources.")

    return source_file_list, source_file_git_list


def annotate(source_files: list[str], dest_files: list[str], repo: str, name: str, revision: str,
             limit_annotations: str = None):
    # Make sure we're at the right revision
    run(f"git -C repos/{repo} checkout {revision}")

    # Create a list of file extensions for source files for C and C++
    c_extensions = [".c", ".h"]
    cpp_extensions = [".cpp", ".hpp", ".hxx", ".cc", ".hh", ".cxx"]
    other_extensions = [".y", ".l"]
    wildcarded_extensions = [f"*{x}" for x in c_extensions + cpp_extensions + other_extensions]
    # Find all files in repos/<repo> with a C or C++ extension
    dir_to_search = f"repos/{repo}"
    if limit_annotations is not None:
        # Strip any trailing slashes from limit_annotations
        limit_annotations = limit_annotations.rstrip("/")
        dir_to_search = f"{dir_to_search}/{limit_annotations}"
    result = run(f"find {dir_to_search} -type f -name {' -o -name '.join(wildcarded_extensions)}",
                 error_msg=f"Failed to find all files in repos/{repo} with a C or C++ extension.")
    # These are our list of source files
    source_files = result.stdout.splitlines()
    # Create a list of destination files
    dest_files = []
    # For each source file, create a destination file
    for source_file in source_files:
        # Strip the <repo> off of the source file
        source_file = source_file[source_file.find(repo) + len(repo) + 1:]
        # Prepend the path to the source file with diffcov/<name>
        dest_file = f"diffcov/{name}/{source_file}"
        # Add the destination file to the list of destination files
        dest_files.append(dest_file)

    for source_file, dest_file in zip(source_files, dest_files):
        # Run the blame.sh script
        # run(f"bash utils/blame.sh repos/{source_file}", error_msg=f"Failed to run blame.sh on repos/{source_file}.")
        # Strip the <repo> off of the source file
        source_file = source_file[source_file.find(repo) + len(repo) + 1:]
        run(f"git -C repos/{repo} blame --line-porcelain {source_file} > repos/{repo}/{source_file}.blame",
            error_msg=f"Failed to blame on repos/{repo}/{source_file}.")
        run(F"git -C repos log -1 --format=%cd --date=short > repos/{repo}/{source_file}.date",
            error_msg=f"Failed to get the date of the last commit on repos/{repo}/{source_file}.")
        subprocess.run(["python3", "utils/parse_git_blame.py", f"repos/{repo}/{source_file}.blame",
                        f"repos/{repo}/{source_file}.date", f"{dest_file}.annotated"], check=True)
        # Remove the blame and date files
        run(f"rm repos/{repo}/{source_file}.blame repos/{repo}/{source_file}.date",
            error_msg=f"Failed to remove repos/{repo}/{source_file}.blame and repos/{repo}/{source_file}.date.")

    # Find all the .annotated files
    result = run(f"find repos/{repo} -name '*.annotated'", error_msg=f"Failed to find all the .annotated files.")
    annotated_files = result.stdout.splitlines()

    # Replace the repos/<repo> part of the path with diffcov/<name>
    annotated_files_dest = [x.replace(f"repos/{repo}", f"diffcov/{name}") for x in annotated_files]

    # Move all the .annotated files to diffcov/<name>
    for annotated_file, annotated_file_dest in zip(annotated_files, annotated_files_dest):
        run(f"mv {annotated_file} {annotated_file_dest}",
            error_msg=f"Failed to move {annotated_file} to {annotated_file_dest}.")

    # Print a message to say that the annotated files have been moved
    print(f"Moved annotated files for {name}.")


def diff(repo: str, baseline: str, current: str, baseline_name: str, current_name: str, source_files: list[str]):
    # Run git diff with these args and place in diffcov/<name>.tmp/diff.txt
    # Checkout the current revision just in case
    run(f"git -C repos/{repo} checkout {current}", error_msg=f"Failed to checkout {current}.")
    # Make a temporary directory inside diffcov/<name> called <name>.tmp
    run(f"mkdir -p diffcov/{repo}-diffcov.tmp", error_msg=f"Failed to make diffcov/{repo}-diffcov.tmp.")
    # Strip the <repo> off of the source files
    source_files = [x[x.find(repo) + len(repo) + 1:] for x in source_files]
    # Decompose the source_files list into a string
    source_files_str = " ".join(source_files)

    # source prefix is the baseline name absolute path
    src_prefix = os.path.abspath(f"diffcov/{baseline_name}")
    # dst prefix is the current name absolute path
    dst_prefix = os.path.abspath(f"diffcov/{current_name}")
    # Make sure both have a trailing slash
    if not src_prefix.endswith("/"):
        src_prefix += "/"
    if not dst_prefix.endswith("/"):
        dst_prefix += "/"

    run(f'git -C repos/{repo} diff {baseline} {current} --src-prefix={src_prefix} '
        f'--dst-prefix={dst_prefix} -- {source_files_str} > diffcov/{repo}-diffcov.tmp/diff.txt ',
        error_msg=f"Failed to run git diff.")

    # Print a message to say that the diff file has been generated
    print(f"Generated diff file for {baseline_name}.")

    # Return the path to the diff file
    return os.path.abspath(f"diffcov/{repo}-diffcov.tmp/diff.txt")


def localize(name: str, path_to_strip: str):
    # Replace the path to the source files in the .info files with the path to the source files in the diffcov folder
    # Generate path_to_replace_with by getting absolute path to diffcov/<name>
    path_to_replace_with = os.path.abspath(f"diffcov/{name}")
    # Find total.info within diffcov/<name>
    result = run(f"find diffcov/{name} -name 'total.info'", error_msg=f"Failed to find total.info.")
    total_info = result.stdout.strip()
    subprocess.run(["python3", "utils/localize_info_src.py", total_info, path_to_strip, path_to_replace_with])

    # Print a message to say that the .info files have been localized
    print(f"Localized .info files for {name}.")

    # Return the absolute path to total.info
    return os.path.abspath(total_info)


def generate_report(repo: str, baseline: str, current: str, current_info_loc: str, baseline_info_loc: str,
                    diff_loc: str, extra_flags: list[str] = None):
    # Create a report for the diff coverage
    print(f"Generating report for {repo}...")
    # Create the name of our report directory
    report_dir = f"diffcov/diffcov-{repo}-baseline-{baseline}-current-{current}"
    report_dir = os.path.abspath(report_dir)
    # Create the report directory
    run(f"rm -rf {report_dir}", error_msg=f"Failed to remove {report_dir}.")
    run(f"mkdir -p {report_dir}", error_msg=f"Failed to create {report_dir}.")
    # Run genhtml

    # Create ignore errors string
    ignore_errors_options = "unmapped,inconsistent"
    if extra_flags is not None:
        ignore_errors_options += ",".join(extra_flags)

    genhtml_cmd = ["genhtml", "--branch-coverage", "--ignore-errors", ignore_errors_options, current_info_loc,
                  "--baseline-file", baseline_info_loc, "--diff-file", diff_loc, "--output-directory", report_dir,
                  "--annotate-script", os.path.abspath("utils/annotate.sh")]
    # result = run(genhtml_cmd,
    #              error_msg=f"Failed to run genhtml.", show_output=True, as_list=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    log_path = f"diffcov/{repo}-diffcov.tmp/genhtml.log"
    with subprocess.Popen(genhtml_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as p:
        with ThreadPoolExecutor(2) as pool:
            r1 = pool.submit(log_popen_pipe, p, p.stdout, filename=log_path)
            r2 = pool.submit(log_popen_pipe, p, p.stderr, filename=log_path)
            r1.result()
            r2.result()

    # Print a message to say that the report has been generated
    print(f"Generated report for {repo} at {os.path.relpath(report_dir)}.")
    print(f"Logs are available at {log_path}.")


def main():
    # parse arguments: repo, archive dir, baseline revision, current revision
    # optional args: source dir

    # TODO: Add a check to figure out if we've got the latest version of lcov installed

    # Check script is run from the root of the repo (i.e. covrig/)
    result = run("realpath .")
    # Check if string ends with covrig
    if not result.stdout.strip().endswith("covrig"):
        print("Please run this script from the root of the repository.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Calculate diff coverage.')
    parser.add_argument('repo', type=str,
                        help='Repository name')
    parser.add_argument('archive', type=str,
                        help='Archive directory (where coverage archives are stored)')
    parser.add_argument('baseline', type=str,
                        help='Baseline revision')
    parser.add_argument('current', type=str,
                        help='Current revision')
    parser.add_argument('--source', type=str, default='',
                        help='Source directory (specify if original lcov was run within a source directory)')
    # add a limit annotations flag that gives the option to limit the annotations to only those that are in a certain directory
    parser.add_argument('--limit-annotations', type=str, default='',
                        help='Limit annotations to only those that are in a certain directory')
    # add a ignore flag that gives the option to ignore certain dirs (like ignore_coverage_from)
    parser.add_argument('--ignore', type=str, default='',
                        help='Ignore certain directories')
    args = parser.parse_args()

    # Strip any trailing slashes from the repo name, archive directory, and source directory
    args.repo = args.repo.rstrip("/")
    args.archive = args.archive.rstrip("/")
    args.source = args.source.rstrip("/")

    # check if archive directory exists
    if not os.path.isdir(args.archive):
        print("Archive directory does not exist.")
        sys.exit(1)

    # Check repos directory exists
    if not os.path.isdir("repos"):
        print("repos directory does not exist.")
        sys.exit(1)

    # Check if repos/<repo> exists
    if not os.path.isdir(f"repos/{args.repo}"):
        print(f"repos/{args.repo} does not exist.")
        sys.exit(1)

    # Check if source specified then repos/<repo>/<source> exists
    if args.source != "":
        if not os.path.isdir(f"repos/{args.repo}/{args.source}"):
            print(f"repos/{args.repo}/{args.source} does not exist.")
            sys.exit(1)

    # Check if commits <baseline> and <current> exist in the repo
    result = run(f"cd repos/{args.repo} && git rev-parse {args.baseline}")
    if result.returncode != 0:
        print(f"Commit {args.baseline} does not exist in the repo.")
        sys.exit(1)
    result = run(f"cd repos/{args.repo} && git rev-parse {args.current}")
    if result.returncode != 0:
        print(f"Commit {args.current} does not exist in the repo.")
        sys.exit(1)

    # Check that the baseline commit is older than the current commit
    result = run(f"cd repos/{args.repo} && git rev-list --count {args.baseline}..{args.current}")
    if result.returncode != 0:
        print(f"Error running git rev-list: {result.stderr}")
        sys.exit(1)
    if int(result.stdout.strip()) == 0:
        print(f"Baseline commit {args.baseline} is newer than current commit {args.current}.")
        sys.exit(1)

    # Check that args.archive contains coverage archives for both commits (of the form coverage-<commit>.tar.bz2)
    result = run(f"ls {args.archive}/coverage-{args.baseline}.tar.bz2")
    if result.returncode != 0:
        print(f"Cannot find coverage archive for baseline commit {args.baseline}.")
        sys.exit(1)
    result = run(f"ls {args.archive}/coverage-{args.current}.tar.bz2")
    if result.returncode != 0:
        print(f"Cannot find coverage archive for current commit {args.current}.")
        sys.exit(1)

    # Now our checks are complete, we can start building the repo snapshot (snapshots at rev <baseline> and <current>)

    # Create the diffcov directory if it doesn't exist
    if not os.path.isdir("diffcov"):
        os.mkdir("diffcov")

    # Remove any existing diffcov/baseline and diffcov/current directories
    if os.path.isdir(f"diffcov/baseline"):
        shutil.rmtree(f"diffcov/baseline")
    if os.path.isdir(f"diffcov/current"):
        shutil.rmtree(f"diffcov/current")

    # Create diffcov/baseline and diffcov/current directories
    if not os.path.isdir(f"diffcov/baseline"):
        os.mkdir(f"diffcov/baseline")
    if not os.path.isdir(f"diffcov/current"):
        os.mkdir(f"diffcov/current")

    baseline_sfs, baseline_git_sfs = build_repo_snapshot(args.repo, args.archive, args.baseline, 'baseline',
                                                         source=args.source, ignore=args.ignore)
    current_sfs, current_git_sfs = build_repo_snapshot(args.repo, args.archive, args.current, 'current',
                                                       source=args.source, ignore=args.ignore)

    # Print baseline and current source files
    print("Baseline source files: {}".format(baseline_sfs))
    print("Current source files: {}".format(current_sfs))
    print("Current git source files: {}".format(current_git_sfs))

    # Only annotate the source files in the current/ directory
    annotate(current_git_sfs, current_sfs, args.repo, 'current', args.current, args.limit_annotations)

    # Run the diff
    # Get all source files
    combined_git_sfs = list(set(baseline_git_sfs) | set(current_git_sfs))
    diff_loc = diff(args.repo, args.baseline, args.current, 'baseline', 'current', combined_git_sfs)

    # Localize both total.info files
    baseline_total_info_path = localize('baseline', f"/home/{args.repo}")
    current_total_info_path = localize('current', f"/home/{args.repo}")

    # Run lcov's genhtml to generate our differential coverage report
    generate_report(args.repo, args.baseline, args.current, current_total_info_path, baseline_total_info_path, diff_loc)


if __name__ == '__main__':
    main()
