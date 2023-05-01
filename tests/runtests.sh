# Basic test runner for the project - would be nice to be more comprehensive but this is a start.

# Run tests
# ====================
TEST_FILES="tests-offline tests-online"

echo "Starting tests..."

# Assert that this script is being run from the root directory
if [ ! -f "tests/runtests.sh" ]; then
    echo "Please run this script from the root directory"
    exit 1
fi

# Find the number of occurrences of the string # TEST in each file
NUM_TESTS=()
for TEST_FILE in ${TEST_FILES}; do
    T_COUNT=$(grep -c "# TEST" tests/${TEST_FILE}.sh)
    NUM_TESTS+=("$T_COUNT")
    # Print found
    echo "Found ${T_COUNT} tests in ${TEST_FILE}"
done

# Run the tests and have a counter for the test number
COUNT=0
NUM=1
for TEST_FILE in ${TEST_FILES}; do
    # Run the tests
    echo "Running tests in ${TEST_FILE}..."
    bash tests/${TEST_FILE}.sh ${NUM}
    EXIT_CODE=$?
    # Update vars
    NUM=$((NUM+NUM_TESTS[COUNT]))
    COUNT=$((COUNT+1))

    # Break if the exit code is not 0
    if [ ${EXIT_CODE} -ne 0 ]; then
        echo "ERROR: Tests in ${TEST_FILE} exited with code ${EXIT_CODE}"
        exit 1
    fi

    # Print a separator
    echo "===================="

done

# Emit "All tests passed"
echo "All tests passed"