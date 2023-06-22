#!/bin/bash
# Run all the commands that setup up redis up until lcov

# d645757 is baseline - 347ab78 is curr for redis example

echo "Make sure to run this script from the root of the covrig repo!"
echo "As of 05/04/2023, requires latest version of LCOV (v1.16-47-g6ae8e6e) on local machine installed from source, pre-release"

# Start a timer
START=$(date +%s)

ROOT=$(realpath .)

## Check root with user (is this the root of the covrig repo? with Y/n with
#read -p "Is this the root of the covrig repo? (Y/n) " -n 1 -r
#echo
#if [[ ! $REPLY =~ ^[Yy]$ ]]
#then
#  exit 1
#fi

# Take in our input: <repo> <baseline> <current> [source dir]
REPO=$1
ARCHIVE_DIR=$2
BASELINE=$3
CURRENT=$4
SOURCE_DIR=$5

# Check we have 4 or 5 args
if [ $# -lt 4 ] || [ $# -gt 5 ]; then
    echo "Usage: $0 <repo> <coverage-archive-dir> <baseline> <current> [source dir]"
    echo "Example: $0 redis data/redis d645757 347ab78 src"
    echo "Example: $0 memcached data/memcached 671fcca 7d6907e (no source dir as memcached's is the root of the repo)"
    exit 1
fi

# If no source dir is given, assume it is the root of the repo
if [ $# -eq 4 ]; then
    SOURCE_DIR="."
fi

# Explain that you need repos/<repo> to exist and have a src/ directory
echo "Unzipping coverage data for $REPO, baseline: $BASELINE, current: $CURRENT"

#rm -rf baseline
#rm -rf current
#
#mkdir baseline
#mkdir current

# Strip any trailing slashes from archive dir
ARCHIVE_DIR=$(echo "$ARCHIVE_DIR" | sed 's:/*$::')

# Strip any trailing slashes from source dir
SOURCE_DIR=$(echo "$SOURCE_DIR" | sed 's:/*$::')

# Make sure coverage data exists for the baseline and current
if [ ! -f "$ARCHIVE_DIR"/coverage-"${BASELINE}".tar.bz2 ]; then
    echo "Error: $ARCHIVE_DIR/coverage-${BASELINE}.tar.bz2 does not exist"
    exit 1
fi

if [ ! -f "$ARCHIVE_DIR"/coverage-"${CURRENT}".tar.bz2 ]; then
    echo "Error: $ARCHIVE_DIR/coverage-${CURRENT}.tar.bz2 does not exist"
    exit 1
fi

rm -rf "$ROOT"/diffcov/baseline
rm -rf "$ROOT"/diffcov/current

# Do everything in the new diffcov directory
mkdir -p "$ROOT"/diffcov
mkdir -p "$ROOT"/diffcov/baseline
mkdir -p "$ROOT"/diffcov/current

# unzip coverage data, place into tmp2 and baseline
tar xjf "$ARCHIVE_DIR"/coverage-"${BASELINE}".tar.bz2 -C diffcov/baseline
tar xjf "$ARCHIVE_DIR"/coverage-"${CURRENT}".tar.bz2 -C diffcov/current

# navigate to repos/redis
cd "$ROOT"/repos/"$REPO" || echo "Error: $ROOT/repos/$REPO does not exist. Make sure you have a repos/<repo> directory"

# If no source dir is given, assume it is the root of the repo, so the whole repo is copied over
git checkout "$BASELINE"
cp -R "$SOURCE_DIR" "$ROOT"/diffcov/baseline/

git checkout "$CURRENT"
cp -R "$SOURCE_DIR" "$ROOT"/diffcov/current/


# use git blame to annotate the files
echo "Annotating files for $REPO, baseline: $BASELINE, current: $CURRENT"

#TODO: will likely have to do a mkdir -p cvr for curl since everything was done in that directory

DIRS=$(find "$SOURCE_DIR" -type d)
# Strip off the leading ./
DIRS=$(echo "$DIRS" | sed 's:^\./::')

# TODO: This method may work for others as well as apr, but I'm not sure
# If apr, do the following on all possible directories inside apr/
#if [ "$REPO" = "apr" ]; then
  for dir in $DIRS; do
      "$ROOT"/utils/annotate_files.sh "$dir"
      # Check if there are any annotated files
      # Do a find for all files that end in .annotated in the current directory
      # If there are any, move them to the diffcov directory
      ANNOTATED_PRESENT=$(find "$dir" -maxdepth 1 -type f -name "*.annotated")
      if [ -n "$ANNOTATED_PRESENT" ]; then
          mv "$dir"/*.annotated "$ROOT"/diffcov/current/"$dir"
          echo "Moved $dir/*.annotated to $ROOT/diffcov/current/$dir"
      fi
  done
#else
#  "$ROOT"/utils/annotate_files.sh "$SOURCE_DIR" # used to run as . from redis/src, hopefully this works
#  mv "$SOURCE_DIR"/*.annotated "$ROOT"/diffcov/current/"$SOURCE_DIR"
#fi


# do the diff between the <baseline> and the <current>
git diff "$BASELINE" "$CURRENT" --src-prefix=baseline/ --dst-prefix="" -- "$SOURCE_DIR"/*.c "$SOURCE_DIR"/*.h "$SOURCE_DIR"/*.cpp "$SOURCE_DIR"/*.hpp  > ../../diffcov/current/diff.txt

# go back to root of repo
cd "$ROOT" || echo "Error: $ROOT does not exist. Make sure you have a root directory"

# localize the coverage data info
echo "Localizing coverage data for $REPO, baseline: $BASELINE, current: $CURRENT"

# Special case for binutils-gdb: strip /home/binutils instead of /home/binutils-gdb
STRIP="/home/$REPO"
REPLACEB="$(realpath diffcov/baseline)"
REPLACEC="$(realpath diffcov/current)"
if [ "$REPO" = "binutils-gdb" ]; then
    STRIP="/home/binutils"
fi

# Special case for zeromq: strip /home/zeromq4-x instead of /home/zeromq
if [ "$REPO" = "zeromq" ]; then
    STRIP="/home/zeromq4-x"
fi

python3 "$ROOT"/utils/localize_info_src.py diffcov/baseline/total.info $STRIP $REPLACEB

python3 "$ROOT"/utils/localize_info_src.py diffcov/current/total.info $STRIP $REPLACEC

echo "Preparing to run genhtml for $REPO, baseline: $BASELINE, current: $CURRENT"

# while in current, run genhtml
OUTDIR="$ROOT"/diffcov/diffcov-"$REPO"-b_"$BASELINE"-c_"$CURRENT"

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
cd "$ROOT"/diffcov/current

if [ "$REPO" = "lighttpd2" ]; then
  # Use lcov to skip the file src/modules/mod_proxy.c - complains of a gained baseline coverage error otherwise
  lcov  --rc lcov_branch_coverage=1 -r total.info "*/src/modules/mod_proxy.c" -o total.info
fi

if [ "$REPO" = "curl" ]; then
  # Skip the file lib/imap.c, complains about the author "ehlertjd" not responsible for any GNC lines
  lcov  --rc lcov_branch_coverage=1 -r total.info "*/lib/imap.c" -o total.info
fi

COMMAND_DUMP="$ROOT"/diffcov/genhtml_output_"$REPO".txt

# NOTE: There is no authoritative way to judge whether genhtml works fully - when running best to check that a minimal number of warnings/errors are printed and nothing looks unreasonable
genhtml --branch-coverage --ignore-errors unmapped,inconsistent,annotate,source,path --synthesize-missing total.info --baseline-file "$ROOT"/diffcov/baseline/total.info --diff-file diff.txt --output-directory "$OUTDIR" --annotate-script "$ROOT"/utils/annotate.sh 2>&1 | tee $COMMAND_DUMP

# Stop the timer
END=$(date +%s)

# Print the time taken
echo "Time taken: $((END-START)) seconds"

# Print the location of the diffcov report
echo "The diffcov report can be found at: diffcov/diffcov-${REPO}-b_${BASELINE}-c_${CURRENT}/index.html"

# Append the command run to the end of the file we wrote the results of genhtml to
echo "Command run:" "$0 $REPO $ARCHIVE_DIR $BASELINE $CURRENT" "$SOURCE_DIR" >> "$COMMAND_DUMP"

echo "Log at: $COMMAND_DUMP"