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

# if fourth arg is set, use it as the image name
if [ "$#" -eq 4 ]; then
  IMAGE=$4
else
  IMAGE=$REPO
fi

# Check we have 3 or 4 args
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo "Usage: run_analytics_parallel.sh <repo> <num_commits> <num_processes> [image]"
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

# Get the remainder
REMAINDER=$((NUM_COMMITS % NUM_PROCESSES))

# Create an array of length NUM_PROCESSES, and fill it with NUM_COMMITS_PER_PROCESS
NCPP_ARRAY=()
for I in $(seq "$NUM_PROCESSES")
do
  if [ "$REMAINDER" -gt 0 ]; then
    NCPP_ARRAY+=("$((NUM_COMMITS_PER_PROCESS + 1))")
    REMAINDER=$((REMAINDER - 1))
  else
    NCPP_ARRAY+=("$NUM_COMMITS_PER_PROCESS")
  fi
done

analytics(){
  # Pull the args into variables
  FILENAME=$1
  LIMIT=$2
  REPO=$3
  NUM_COMMITS=$4
  IMAGE=$5
  # Run the analytics
  echo "============================"
  echo "> python3 analytics.py --output $FILENAME --limit $LIMIT --image $IMAGE $REPO $NUM_COMMITS"
  echo "============================"
  python3 analytics.py --output "$FILENAME" --limit "$LIMIT" --image "$IMAGE" "$REPO" "$NUM_COMMITS"
}
export -f analytics

# Start a timer
START_TIME=$(date +%s)

# generate the args we will supply to each process
OUTPUT_FILES=()
COMMIT_RANGES=()

TOTAL=0

for I in $(seq "$NUM_PROCESSES")
do
  OUTPUT_FILES+=("$REPO""$I")
  # Use the NCPP_ARRAY elements to get TOTAL
  TOTAL=$((TOTAL + NCPP_ARRAY[I - 1]))
  COMMIT_RANGES+=("$TOTAL")
done

# Run the analytics in parallel using GNU parallel

rm -rf data/"$REPO"_log.txt

# The -j flag specifies the number of processes to run in parallel
# The -k flag specifies to keep the order of the output
# Test the command first with --dry-run

parallel --link --bar -j "$NUM_PROCESSES" -k analytics {1} {2} "$REPO" {3} "$IMAGE" 2>&1 ::: "${OUTPUT_FILES[@]}" ::: "${NCPP_ARRAY[@]}" ::: "${COMMIT_RANGES[@]}" | tee data/"$REPO"_log.txt

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