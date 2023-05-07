#!/bin/bash
# Run all the commands that setup up redis up until lcov

# d645757 is baseline - 347ab78 is curr for redis example

echo "Make sure to run this script from the root of the covrig repo!"
echo "As of 05/04/2023, requires latest version of LCOV (v1.16-47-g6ae8e6e) on local machine installed from source, pre-release"

# Sleep for 2 seconds to give the user time to read the above
sleep 2

# Start a timer
START=$(date +%s)

ROOT=$(realpath .)

# Check root with user (is this the root of the covrig repo? with Y/n with
read -p "Is this the root of the covrig repo? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
  exit 1
fi

# Take in our input: <repo> <baseline> <current> [source dir]
REPO=$1
ARCHIVE_DIR=$2
BASELINE=$3
CURRENT=$4
SOURCE_DIR=$5

# Check we have 4 or 5 args
if [ $# -lt 4 ] || [ $# -gt 5 ]; then
    echo "Usage: $0 <repo> <coverage-archive-dir> <baseline> <current> [source dir]"
    echo "Example: $0 redis data/parallel_redis d645757 347ab78 src"
    echo "Example: $0 memcached data/memcached d645757 347ab78 (no source dir as memcached's is the root of the repo)"
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

git checkout "$BASELINE"
cp -R "$SOURCE_DIR" "$ROOT"/diffcov/baseline/

git checkout "$CURRENT"
cp -R "$SOURCE_DIR" "$ROOT"/diffcov/current/
# use git blame to annotate the files
"$ROOT"/utils/annotate_files.sh "$SOURCE_DIR" # used to run as . from redis/src, hopefully this works
mv "$SOURCE_DIR"/*.annotated "$ROOT"/diffcov/current/"$SOURCE_DIR"


# do the diff between the <baseline> and the <current>
git diff "$BASELINE" "$CURRENT" --src-prefix=baseline/ --dst-prefix="" -- "$SOURCE_DIR"/*.c "$SOURCE_DIR"/*.h "$SOURCE_DIR"/*.cpp "$SOURCE_DIR"/*.hpp  > ../../diffcov/current/diff.txt

# go back to root of repo
cd "$ROOT" || echo "Error: $ROOT does not exist. Make sure you have a root directory"

# localize the coverage data info
python3 "$ROOT"/utils/localize_info_src.py diffcov/baseline/total.info /home/"$REPO" "$(realpath diffcov/baseline)"

python3 "$ROOT"/utils/localize_info_src.py diffcov/current/total.info /home/"$REPO" "$(realpath diffcov/current)"

# while in current, run genhtml
rm -rf "$ROOT"/diffcov/diffcov-"$REPO"-b_"$BASELINE"-c_"$CURRENT"
mkdir -p "$ROOT"/diffcov/diffcov-"$REPO"-b_"$BASELINE"-c_"$CURRENT"
cd "$ROOT"/diffcov/current
genhtml --branch-coverage --ignore-errors unmapped,inconsistent total.info --baseline-file "$ROOT"/diffcov/baseline/total.info --diff-file diff.txt --output-directory "$ROOT"/diffcov/diffcov-"$REPO"-b_"$BASELINE"-c_"$CURRENT" --annotate-script "$ROOT"/utils/annotate.sh

# Stop the timer
END=$(date +%s)

# Print the time taken
echo "Time taken: $((END-START)) seconds"

# Print the location of the diffcov report
echo "The diffcov report can be found at: diffcov/diffcov-${REPO}-b_${BASELINE}-c_${CURRENT}/index.html"