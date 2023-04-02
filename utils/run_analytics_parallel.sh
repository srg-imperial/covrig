#!/bin/bash

# This script is used to run the analytics in parallel.
# It takes as input a repository, a start commit and a number of commits.
# It then runs the analytics on the specified number of commits starting from the start commit.

# Usage: run_analytics_parallel.sh <repo> <num_commits> <num_processes>

# Example: run_analytics_parallel.sh redis 100 4

# The script will create a directory for each process in the output directory.
# Each directory will contain the output of the analytics for the commits assigned to that process.

# Pull all the args into variables
REPO=$1
NUM_COMMITS=$2
NUM_PROCESSES=$3

# Check we have 3 args
if [ "$#" -ne 3 ]; then
  echo "Usage: run_analytics_parallel.sh <repo> <num_commits> <num_processes>"
  exit 1
fi

# Assert the current directory is the root of the repository
if [ ! -f utils/run_analytics_parallel.sh ]; then
  echo "Please run this script from the root of the repository"
  exit 1
fi

mkdir -p data

OUT_DIR="data/parallel_""$REPO"

# If the output directory already exists, ask the user if they want to overwrite it
if [ -d "$OUT_DIR" ]; then
  read -p "The output directory already exists. Do you want to overwrite it? (Y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
    exit 1
  fi
  rm -rf "$OUT_DIR"
fi

# Create the output directory
mkdir -p "$OUT_DIR"

NUM_COMMITS_PER_PROCESS=$((NUM_COMMITS / NUM_PROCESSES)) # Integer division

analytics(){
  # Pull the args into variables
  FILENAME=$1
  LIMIT=$2
  REPO=$3
  NUM_COMMITS=$4
  # Run the analytics
  python analytics.py --output "$FILENAME" --limit "$LIMIT" --image "$REPO" "$REPO" "$NUM_COMMITS"
}

# Start a timer
START_TIME=$(date +%s)

for I in $(seq "$NUM_PROCESSES")
do
  analytics "$REPO""$I" $NUM_COMMITS_PER_PROCESS "$REPO" $((I * NUM_COMMITS_PER_PROCESS)) &
done
wait

echo "Done running analytics, merging files..."

# Merge the files

# Now merge all the directories into one
FIRST_DIR="data/""$REPO""1"

# Get the name of the csv file inside "data"/"$REPO"
CSV_FILE_NAME=$(find "$FIRST_DIR" -name "*.csv" -printf "%f\n")

OUT_FILE="$OUT_DIR"/"$CSV_FILE_NAME"

# Get the first line of one of the files and write it to the output file (also create the output file in the process)
head -n 1 "$FIRST_DIR"/"$CSV_FILE_NAME" > "$OUT_FILE"

# Merge the files in reverse order
for I in $(seq "$NUM_PROCESSES" -1 1)
do
  # Remove the first line of the csv file
  tail -n +2 "data/""$REPO""$I"/"$CSV_FILE_NAME" >> "$OUT_FILE"
  # Copy over all the tar files
  cp -r "data/""$REPO""$I"/*.tar.bz2 "$OUT_DIR"
  rm -rf "data/""$REPO""$I"
done

# Finish the timer
END_TIME=$(date +%s)

echo "Done in $((END_TIME - START_TIME)) seconds! The files are in the data directory under parallel_${REPO}."