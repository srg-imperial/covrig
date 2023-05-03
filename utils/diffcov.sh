#!/bin/bash
# TODO: run this and formalize this as a proper script - atm this is just a bunch of commands that I ran to get index.html
# Run all the commands that setup up redis up until lcov

# d645757 is baseline - 347ab78 is curr

echo "Make sure to run this script from the root of the covrig repo!"
echo "As of 05/04/2023, requires latest version of LCOV (v1.16-47-g6ae8e6e) on local machine installed from source, pre-release"

# Sleep for 2 seconds to give the user time to read the above
sleep 2

# Start a timer
START=$(date +%s)

ROOT=$(realpath .)

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

rm -rf tmp2-baseline
rm -rf tmp2-current

mkdir tmp2-baseline
mkdir tmp2-current

# unzip coverage data, place into tmp2 and tmp2-baseline
tar xjf "$ARCHIVE_DIR"/coverage-"${BASELINE}".tar.bz2 -C tmp2-baseline
tar xjf "$ARCHIVE_DIR"/coverage-"${CURRENT}".tar.bz2 -C tmp2-current



# navigate to repos/redis
cd "$ROOT"/repos/"$REPO" || echo "Error: $ROOT/repos/$REPO does not exist. Make sure you have a repos/<repo> directory"

git checkout "$BASELINE"
cp -R "$SOURCE_DIR" "$ROOT"/tmp2-baseline/

git checkout "$CURRENT"
cp -R "$SOURCE_DIR" "$ROOT"/tmp2-current/
# use git blame to annotate the files
"$ROOT"/utils/annotate_files.sh "$SOURCE_DIR" # used to run as . from redis/src, hopefully this works
mv "$SOURCE_DIR"/*.annotated "$ROOT"/tmp2-current/"$SOURCE_DIR"


# do the diff between the <baseline> and the <current>
git diff "$BASELINE" "$CURRENT" --src-prefix=tmp2-baseline/ --dst-prefix="" -- "$SOURCE_DIR"/*.c "$SOURCE_DIR"/*.h "$SOURCE_DIR"/*.cpp "$SOURCE_DIR"/*.hpp  > ../../tmp2-current/diff.txt

# go back to root of repo
cd "$ROOT"

# localize the coverage data info
python3 "$ROOT"/utils/localize_info_src.py tmp2-baseline/total.info /home/"$REPO" $(realpath tmp2-baseline)

python3 "$ROOT"/utils/localize_info_src.py tmp2-current/total.info /home/"$REPO" $(realpath tmp2-current)

# while in tmp2-current, run genhtml
rm -rf "$ROOT"/diffcov-"$REPO"-b_"$BASELINE"-c_"$CURRENT"
mkdir -p "$ROOT"/diffcov-"$REPO"-b_"$BASELINE"-c_"$CURRENT"
cd "$ROOT"/tmp2-current
genhtml --branch-coverage --ignore-errors unmapped,inconsistent total.info --baseline-file "$ROOT"/tmp2-baseline/total.info --diff-file diff.txt --output-directory "$ROOT"/diffcov-"$REPO"-b_"$BASELINE"-c_"$CURRENT" --annotate-script "$ROOT"/utils/annotate.sh

# Stop the timer
END=$(date +%s)

# Print the time taken
echo "Time taken: $((END-START)) seconds"

# Print the location of the diffcov report
echo "The diffcov report can be found at: diffcov-${REPO}-b_${BASELINE}-c_${CURRENT}/index.html"