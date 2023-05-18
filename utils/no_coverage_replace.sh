# In the unlikely event we get a large number of revisions that spuriously suggest NoCoverage, identify them

# This script is intended to be run from the root of the repository

CSV_FILE=$1

# Get the list of revisions that have been marked as NoCoverage in the CSV file
# String to filter
FILTER_STRING="NoCoverage"

# Ignore the first line (header)

# get the commit hash (the bit before the first comma on each line) for all lines that contain the string NoCoverage
FILTERED_ROWS=()

# Read the CSV file line by line
while IFS= read -r line; do
  # Check if the line contains the filter string
  if [[ $line == *"$FILTER_STRING"* ]]; then
    # Append the line to the output file
    FILTERED_ROWS+=("$line")
  fi
done < "$CSV_FILE"

echo "Found ${#FILTERED_ROWS[@]} revisions that have been marked as NoCoverage"

COMMIT_HASHES=()

# For each row in FILTERED_ROWS, get the commit hash (the bit before the first comma on each line)
for row in "${FILTERED_ROWS[@]}"; do
  # Extract the substring before the first comma
  COMMIT_HASHES+=("${row%%,*}")
done

# Print the commit hashes
echo "Commit hashes:"
printf '%s\n' "${COMMIT_HASHES[@]}"

# Save them to a file called no_coverage_revisions.txt
printf '%s\n' "${COMMIT_HASHES[@]}" > no_coverage_revisions.txt