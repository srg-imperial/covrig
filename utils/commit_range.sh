#!/bin/bash

# Run this from a repo (i.e. in repos/redis, run ../../utils/commit_range.sh <commit hash> <number of commits to jump forward>)

# Input is a commit hash
INPUT_HASH=$1
# Number of commits to jump forward
JUMP=$2

# Make sure JUMP is at least 1
if [ $JUMP -lt 1 ]; then
    echo "JUMP must be at least 1"
    exit 1
fi

# Make sure we are in a git repo
if [ ! -d .git ]; then
    echo "Not in a git repo"
    exit 1
fi

# Print the name of the git repo we are in
echo "Looking at commits in repo: $(basename $(git rev-parse --show-toplevel))"

# Get all commit hashes in the current branch
git rev-list --first-parent HEAD > /tmp/commit_hashes

# Find the line number of the input hash
LINE_NUMBER=$(grep -n $INPUT_HASH /tmp/commit_hashes | cut -d: -f1)

# Get the hash of the commit JUMP commits ahead of the input hash
OUTPUT_HASH=$(sed -n "$(($LINE_NUMBER - $JUMP + 1))p" /tmp/commit_hashes)

# Output the hash
echo To analyze $JUMP revisions including $INPUT_HASH as the first, use $OUTPUT_HASH

# Remove the temporary file
rm /tmp/commit_hashes
