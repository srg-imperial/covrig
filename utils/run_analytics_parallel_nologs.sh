#!/bin/bash

# This script is used to run the analytics in parallel.
# It takes as input a repository, a start commit and a number of commits.
# It then runs the analytics on the specified number of commits starting from the start commit.

# Usage: run_analytics_parallel.sh <repo> <num_commits> <num_processes> <image> <final_commit>

# Example: run_analytics_parallel.sh redis 100 4 redis12
# Example: run_analytics_parallel.sh memcached 391 4 memcached12 e1c93df

# The script will create a directory for each process in the output directory.
# Each directory will contain the output of the analytics for the commits assigned to that process.

# Pull all the args into variables
REPO=$1
NUM_COMMITS=$2
NUM_PROCESSES=$3
IMAGE=$4

# if fifth arg is given, use it as the commit to end at
if [ "$#" -eq 5 ]; then
  FINAL_COMMIT=$5
fi

# Check we have 3 or 4 args
if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
  echo "Usage: run_analytics_parallel.sh <repo> <num_commits> <num_processes> <image> [commit]"
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
#  rm -rf "data/""$REPO""_logs"
#  rm -rf "data/""$REPO""_logs.zip"
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
  FINAL_COMMIT=$6
  # Run the analytics
  echo "============================"
  echo "> python3 analytics.py --output $FILENAME --limit $LIMIT --image $IMAGE $REPO $NUM_COMMITS"
  echo "============================"
  # If the final commit is not specified, don't provide --endatcommit
  if [ -z "$FINAL_COMMIT" ]; then
    python3 analytics.py --output "$FILENAME" --limit "$LIMIT" --image "$IMAGE" "$REPO" "$NUM_COMMITS"
  else
    python3 analytics.py --output "$FILENAME" --limit "$LIMIT" --image "$IMAGE" --endatcommit "$FINAL_COMMIT" "$REPO" "$NUM_COMMITS"
  fi
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
  # Remove all the output directories just in case
  rm -rf "data/""$REPO""$I"
done

# Run the analytics in parallel using GNU parallel

#rm -rf data/"$REPO"_log.txt

# The -j flag specifies the number of processes to run in parallel
# The -k flag specifies to keep the order of the output
# Test the command first with --dry-run

#rm -rf data/"$REPO"_logs
#mkdir -p "data/""$REPO""_logs"

parallel --link -j "$NUM_PROCESSES" -k analytics {1} {2} "$REPO" {3} "$IMAGE" "$FINAL_COMMIT" ::: "${OUTPUT_FILES[@]}" ::: "${NCPP_ARRAY[@]}" ::: "${COMMIT_RANGES[@]}" &
pid=$!

# Kill the parallel process if script killed
trap "kill $pid 2> /dev/null" EXIT

# Wait for the parallel process to finish, and check the number of processes running
while kill -0 $pid 2> /dev/null; do
    SUM=0
    for I in $(seq "$NUM_PROCESSES")
    do
      # Check if the directory exists and is not empty
      if [ -d "data/""$REPO""$I" ] && [ "$(ls -A "data/""$REPO""$I")" ]; then
        # Get the name of the csv file inside "data"/"$REPO""$I", that is "$REPO" with the first letter uppercase and all the other letters lowercase
        CSV_FILE_NAME=$(find "data/""$REPO""$I" -name "*.csv" -printf "%f\n")
        if [ -n "$CSV_FILE_NAME" ]; then
          # Add the number of lines in the csv file to the sum, minus 1 because the first line is the header
          SUM=$((SUM + $(cat "data/""$REPO""$I""/""$CSV_FILE_NAME" | wc -l) - 1))
        fi
      fi
    done
    # Print the number of commits explored so far and the number of commits left to explore (in the same line)
    echo -ne "Analytics running, ${SUM}/${NUM_COMMITS} revisions explored so far...\033[0K\r"
    sleep 15
done

echo -ne "\033[0K\r"
echo "============================"

# Disable the trap if the script exits normally
trap - EXIT

echo "Done running analytics, merging files..."

# Merge the files

# Now merge all the directories into one
FIRST_DIR="data/""$REPO""1"

# Get the name of the csv file inside "data"/"$REPO"
CSV_FILE_NAME=$(find "$FIRST_DIR" -name "*.csv" -printf "%f\n")

OUT_FILE="$OUT_DIR"/"$CSV_FILE_NAME"

# Get the first line of one of the files and write it to the output file (also create the output file in the process)
head -n 1 "$FIRST_DIR"/"$CSV_FILE_NAME" > "$OUT_FILE"

OUT_MSG=""

# Merge the files in reverse order
for I in $(seq "$NUM_PROCESSES" -1 1)
do
  # Remove the first line of the csv file
  tail -n +2 "data/""$REPO""$I"/"$CSV_FILE_NAME" >> "$OUT_FILE"
  # Copy over all the tar files

  # Get all tar.bz2 files in the directory
  TAR_FILE_NAME=$(find "data/""$REPO""$I" -name "*.tar.bz2" -printf "%f\n")
  if [ -z "$TAR_FILE_NAME" ]; then
    OUT_MSG="Warning: No tar.bz2 files found for parallel partition ${I}.\n${OUT_MSG}"
  else
  # Copy all the tar.bz2 files to the output directory
  find "data/""$REPO""$I" -name "*.tar.bz2" -exec cp {} "$OUT_DIR" \;
  fi
  rm -rf "data/""$REPO""$I"
done

# Print the output message
echo -ne "$OUT_MSG"

# Finish the timer
END_TIME=$(date +%s)

NUM_FILES=$(ls -1 "$OUT_DIR" | wc -l)
#echo "Log files are in "data/""$REPO""_logs"."

## Zip the log directory
#zip -r "data/""$REPO""_logs.zip" "data/""$REPO""_logs"

# Get the number of lines in the output file - 1
NUM_LINES=$(( $(wc -l < "$OUT_FILE") - 1 ))

echo "Successfully analyzed ${NUM_LINES}/${NUM_COMMITS} revisions."
echo "Created $((NUM_FILES - 1)) archives in ${OUT_DIR} for each revision that compiled/had coverage data."
echo "Done in $((END_TIME - START_TIME)) seconds! The data files are in the data directory under parallel_${REPO}."