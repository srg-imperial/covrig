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
ARGS=("$@")

# If no args or less than 5 args are provided, print the usage and exit
if [ $# -lt 4 ]; then
  echo "Usage: ./run_analytics_parallel_certainrevs.sh <repo> <image> <repeats> <commits>"
  echo "Example: ./utils/run_analytics_parallel_certainrevs.sh redis redis:14 5 09aa55a,2f49734,1b13adf"
  echo "Example: ./utils/run_analytics_parallel_certainrevs.sh zeromq zeromq:14 5 5ef6331,65b6351,f7bd543"
  exit 1
fi

# The first arg is the repository
REPO=${ARGS[0]}
# The second arg is the image
IMAGE=${ARGS[1]}
# The third arg is the repeats arg
REPEATS=${ARGS[2]}
# The remaining arg is a comma-separated list of commits
COMMITS=${ARGS[3]}

# Pull COMMITS into an array
IFS=',' read -r -a COMMIT_ARRAY <<< "$COMMITS"

# The number of commits is the length of the array
NUM_COMMITS=${#COMMIT_ARRAY[@]}

echo "Running analytics on $NUM_COMMITS commits"

# Assert the current directory is the root of the repository
if [ ! -f utils/run_analytics_parallel.sh ]; then
  echo "Please run this script from the root of the repository"
  exit 1
fi

mkdir -p data

OUT_DIR="data/${REPO}1"

# If the output directory already exists, ask the user if they want to overwrite it
if [ -d "$OUT_DIR" ]; then
  read -p "The output directory already exists. Do you want to overwrite it? (Y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
    exit 1
  fi
  for I in $(seq "$REPEATS")
  do
    rm -rf "data/${REPO}""$I"
  done
fi

# Create the output directory
mkdir -p "$OUT_DIR"

# Create an array of output files
OUTPUT_FILES=()

analytics(){
  # Pull the args into variables
  FILENAME=$1
  REPO=$2
  IMAGE=$3
  COMMITS_FOR_PROCESS=$4
  # Run the analytics

  # Extract COMMITS_FOR_PROCESS into an array
  IFS=',' read -r -a COMMITS <<< "$COMMITS_FOR_PROCESS"

  for FINAL_COMMIT in "${COMMITS[@]}"
  do
    echo "============================"
    echo "> python3 analytics.py --output $FILENAME --image $IMAGE --endatcommit $FINAL_COMMIT $REPO 1"
    echo "============================"
    python3 analytics.py --output "$FILENAME" --image "$IMAGE" --endatcommit "$FINAL_COMMIT" "$REPO" 1
  done
}
export -f analytics

# Start a timer
START_TIME=$(date +%s)

for I in $(seq "$REPEATS")
do
  OUTPUT_FILES+=("$REPO""$I")
done

# Run the analytics in parallel using GNU parallel

# The -j flag specifies the number of processes to run in parallel
# The -k flag specifies to keep the order of the output
# Test the command first with --dry-run

parallel --link -j "$REPEATS" -k analytics {1} "$REPO" "$IMAGE" {2} ::: "${OUTPUT_FILES[@]}" ::: "${COMMITS[@]}" &
pid=$!

# Kill the parallel process if script killed
trap "kill $pid 2> /dev/null" EXIT

# Wait for the parallel process to finish, and check the number of processes running
while kill -0 $pid 2> /dev/null; do
    SUM=0
    # Check if the directory exists and is not empty
    if [ -d "data/""$REPO""1" ] && [ "$(ls -A "data/""$REPO""1")" ]; then
      # Get the name of the csv file inside "data"/"$REPO""$I", that is "$REPO" with the first letter uppercase and all the other letters lowercase
      CSV_FILE_NAME=$(find "data/""$REPO""1" -name "*.csv" -printf "%f\n")
      if [ -n "$CSV_FILE_NAME" ]; then
        # Add the number of lines in the csv file to the sum, minus 1 because the first line is the header
        SUM=$((SUM + $(cat "data/""$REPO""1""/""$CSV_FILE_NAME" | wc -l) - 1))
      fi
    fi
    # Print the number of commits explored so far and the number of commits left to explore (in the same line)
    echo -ne "Analytics running, ${SUM}/${NUM_COMMITS} revisions explored so far...\033[0K\r"
    sleep 15
done

echo -ne "\033[0K\r"
echo "============================"

# Disable the trap if the script exits normally
trap - EXIT

echo "Done running analytics, files will be in $OUT_DIR(1,2,...,$REPEATS)"
#
## Merge the files
#
## Now merge all the directories into one
#FIRST_DIR="data/""$REPO""1"
#
## Get the name of the csv file inside "data"/"$REPO"
#CSV_FILE_NAME=$(find "$FIRST_DIR" -name "*.csv" -printf "%f\n")
#
#OUT_FILE="$OUT_DIR"/"$CSV_FILE_NAME"
#
## Get the first line of one of the files and write it to the output file (also create the output file in the process)
#head -n 1 "$FIRST_DIR"/"$CSV_FILE_NAME" > "$OUT_FILE"
#
#OUT_MSG=""
#
## Merge the files in reverse order
#for I in $(seq "$NUM_PROCESSES" -1 1)
#do
#  # Remove the first line of the csv file
#  tail -n +2 "data/""$REPO""$I"/"$CSV_FILE_NAME" >> "$OUT_FILE"
#  # Copy over all the tar files
#
#  # Get all tar.bz2 files in the directory
#  TAR_FILE_NAME=$(find "data/""$REPO""$I" -name "*.tar.bz2" -printf "%f\n")
#  if [ -z "$TAR_FILE_NAME" ]; then
#    OUT_MSG="Warning: No tar.bz2 files found for parallel partition ${I}.\n${OUT_MSG}"
#  else
#  # Copy all the tar.bz2 files to the output directory
#  find "data/""$REPO""$I" -name "*.tar.bz2" -exec cp {} "$OUT_DIR" \;
#  fi
#  rm -rf "data/""$REPO""$I"
#done
#
## Print the output message
#echo -ne "$OUT_MSG"
#
## Finish the timer
#END_TIME=$(date +%s)
#
#NUM_FILES=$(ls -1 "$OUT_DIR" | wc -l)
##echo "Log files are in "data/""$REPO""_logs"."
#
### Zip the log directory
##zip -r "data/""$REPO""_logs.zip" "data/""$REPO""_logs"
#
## Get the number of lines in the output file - 1
#NUM_LINES=$(( $(wc -l < "$OUT_FILE") - 1 ))
#
#echo "Successfully analyzed ${NUM_LINES}/${NUM_COMMITS} revisions."
#echo "Created $((NUM_FILES - 1)) archives in ${OUT_DIR} for each revision that compiled/had coverage data."
#echo "Done in $((END_TIME - START_TIME)) seconds! The data files are in the data directory under parallel_${REPO}."