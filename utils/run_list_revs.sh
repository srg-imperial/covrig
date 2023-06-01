# Shell script that runs a list of revisions given by the first argument (text file, one commit hash per line)

# This script is intended to be run from the root of the repository

LIST_REVS_FILE=$1
NUM_PROCESSES=$2
OUTPUT_DIR=$3
REPO=$4
IMAGE=$5
REPEATS=$6

# Print usage if the number of args is incorrect
if [ "$#" -lt 5 ] || [ "$#" -gt 6 ]; then
  echo "Usage: run_list_revs.sh <list_revs_file> <jobs> <output_dir> <repo> <image> [repeats]"
  exit 1
fi

# Extract LIST_REVS_FILE into an array
LIST_REVS=()

# Read the LIST_REVS_FILE line by line
while IFS= read -r line; do
  # Append the line to the output file
  LIST_REVS+=("$line")
done < "$LIST_REVS_FILE"

# Get the number of commits, and split them into NUM_PROCESSES groups
NUM_COMMITS="${#LIST_REVS[@]}"
echo "Found $NUM_COMMITS commits"

# Integer divison
NUM_COMMITS_PER_PROCESS=$((NUM_COMMITS / NUM_PROCESSES))

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

# Print the NCPP_ARRAY
echo "NCPP_ARRAY:"
for I in $(seq "$NUM_PROCESSES")
do
  echo "${NCPP_ARRAY[$((I - 1))]}"
done

# Make the output directory in data/ if it doesn't exist
mkdir -p data/"$OUTPUT_DIR"

# Get cumulative indices from NCPP_ARRAY
# e.g. if NCPP_ARRAY is [2,1,1], then CUMULATIVE_INDICES is [0,2,3]
CUMULATIVE_INDICES=()
CUMULATIVE_INDICES+=("0")
for I in $(seq "$NUM_PROCESSES")
do
  CUMULATIVE_INDICES+=("$((CUMULATIVE_INDICES[$((I - 1))] + NCPP_ARRAY[$((I - 1))]))")
done

# Print the CUMULATIVE_INDICES
echo "CUMULATIVE_INDICES:"
for I in $(seq "$NUM_PROCESSES")
do
  echo "${CUMULATIVE_INDICES[$((I - 1))]}"
done

# Add the last elem (length of LIST_REVS) to CUMULATIVE_INDICES
CUMULATIVE_INDICES+=("$NUM_COMMITS")

# Remove the first elem (0) from CUMULATIVE_INDICES
CUMULATIVE_INDICES=("${CUMULATIVE_INDICES[@]:1}")

split_strings=()
start_index=0
for index in "${CUMULATIVE_INDICES[@]}"; do
  # Exit if start_index == index
  if [ "$start_index" -eq "$index" ]; then
    break
  fi
  # Slice the LIST_REVS array from start_index to index
  substring="${LIST_REVS[@]:start_index:index-start_index}"
  start_index="$index"
  split_strings+=("$substring")
done

# Print the split_strings
echo "split_strings:"
for I in $(seq "$NUM_PROCESSES")
do
  echo "${split_strings[$((I - 1))]}"
done

analytics(){
  # Pull the args into variables
  FILENAME=$1
  REPO=$2
  IMAGE=$3
  REVISION_LIST=$4
  REPEATS=$5
  # If the final commit is not specified, don't provide --endatcommit
  for REV in $REVISION_LIST
  do
    echo "================================="
    echo "Running analytics.py for $REV"
    echo "================================="
    if [ -z "$REPEATS" ]; then
      python3 analytics.py --output "$FILENAME" --image "$IMAGE" --endatcommit "$REV" "$REPO" 1
    else
      python3 analytics.py --output "$FILENAME" --image "$IMAGE" --endatcommit "$REV" --repeats "$REPEATS" "$REPO" 1
    fi
    sleep 0.1
  done

}
export -f analytics

# Start a timer
START_TIME=$(date +%s)

# Run each revision in LIST_REVS in parallel using GNU parallel with JOBS jobs
parallel --link -j "$NUM_PROCESSES" -k analytics "$OUTPUT_DIR" "$REPO" "$IMAGE" {1} "$REPEATS" ::: "${split_strings[@]}" &
pid=$!

# Kill the parallel process if script killed
trap "kill $pid 2> /dev/null" EXIT

# Wait for the parallel process to finish, and check the number of processes running
while kill -0 $pid 2> /dev/null; do
    SUM=0
    # Look at $OUTPUT_DIR/"$REPO".csv and count the number of lines - 1
    # See if there is a csv file in data/"$OUTPUT_DIR"
    SEARCH=$(find data/"$OUTPUT_DIR" -name "*.csv")

    # If SEARCH is non-empty, then there is a csv file in data/"$OUTPUT_DIR", so count the number of lines - 1
    # Get the name of the file
    if [ -n "$SEARCH" ]; then
      FILENAME=$(basename "$SEARCH")
      SUM=$(wc -l < data/"$OUTPUT_DIR"/"$FILENAME")
      SUM=$((SUM - 1))
    fi
    # Print the number of commits explored so far and the number of commits left to explore (in the same line)
    echo -ne "Analytics running, ${SUM}/${NUM_COMMITS} revisions explored so far...\033[0K\r"
    sleep 15
done

echo -ne "\033[0K\r"
echo "============================"

# Disable the trap if the script exits normally
trap - EXIT

# End the timer
END_TIME=$(date +%s)

echo "Took $((END_TIME - START_TIME)) seconds to run analytics on $NUM_COMMITS revisions with $REPEATS repeats"
echo "Done running analytics, output csv found in data/$OUTPUT_DIR/$REPO.csv"
