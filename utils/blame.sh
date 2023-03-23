#!/bin/bash

# Run git blame on all of the source files in the repo (.c, .h, .cpp, .hpp)
# and generate a file with the following format:
# commit|who|days|line
# where commit is the commit hash, who is the author, days is the number of days since the commit, and line is the line of code
# This file is then used by utils/annotate.sh

ORIGIN=$(realpath .)

# get location of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# if no args are passed in, print usage
if [ $# -eq 0 ]; then
    echo "Usage: ./blame.sh <repo> [--all|--targets <targets>]"
    echo "Example: ./blame.sh ../redis src/ae.c"
    exit 1
fi

# Extract repo location from first arg
FILE=$1

# define our targets with a cmd line option, --all or default being a since file


# Print the targets
echo "Running git blame on $FILE $(realpath .)"

# Run git blame and capture the commit hash, author, date, and line of code
#use sed to get the commit hash, author, date and the line
#git blame --line-porcelain "$TARGETS" | sed -r '/^[0-9a-f]{40}\b/!d;:a;/\ncommitter-time\b/bb;$!{N;ba};:b;s/\s+.*(\s.*)/\1/'
#git blame --line-porcelain "$TARGETS" | sed -r '/^[0-9a-f]{40}\b/!d;:a;/\nauthor\b/bb;$!{N;ba};:b;s/\s+.*(\s.*)/\1/'

git blame --line-porcelain "$FILE" > rawblame.txt

# note we
# Run git log to get the current date
git log -1 --format=%cd --date=short > date.txt

# run parse_git_blame.py on the raw blame file
python $DIR/parse_git_blame.py rawblame.txt date.txt blame.txt

# rename the blame file to (effectively) target.c.annotated
mv blame.txt $FILE.annotated

# TODO: remove the rawblame.txt and date.txt files

# TODO: use the blame.txt file to annotate the source files by passing our file into utils/annotate.sh?

# Go back to the original directory
cd $ORIGIN

# Output the blame file
#cat blame.txt