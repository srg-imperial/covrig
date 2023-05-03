# First arg is a counter for the test number
NUM=$1

# TEST OFFLINE
# ====================

# Check if repos/lighttpd2 exists
if [ ! -d repos/lighttpd2 ]; then
    # Should be done by build script on GitHub Actions
    echo "Failed, repos/lighttpd2 does not exist"
    exit 1
fi

# Create data/lighttpd2 directory if it doesn't exist
mkdir -p data/lighttpd2

# Copy the coverage-0d40b25.tar.bz2 (lighttpd2 coverage archive) to data/lighttpd2
cp tests/data/coverage-0d40b25.tar.bz2 data/lighttpd2

# Run the tests and make sure it succeeds
mkdir -p tests/logs

# Create a log file for this test named after the filename and remove the extension .sh
LOGFILE=tests/logs/"$(basename "$0" .sh)".log

echo -n "#${NUM} Covrig offline test: "
python3 analytics.py --output lighttpd2 --offline --endatcommit 0d40b25 lighttpd2 1 &> ${LOGFILE}
if [ $? -ne 0 ]; then
    echo "Failed, see ${LOGFILE} for details"
    exit 1
fi

# Make sure the csv file exists
if [ ! -f data/lighttpd2/Lighttpd2Offline.csv ]; then
    echo "Failed, see ${LOGFILE} for details"
    exit 1
fi

# If it succeeds, then we're good
echo "Succeeded"

# Update vars
NUM=$((NUM+1))

# TEST CORRECTNESS
# ====================

# Inspect the csv file and make sure it's correct
OFFLINE_CORRECT_STRING="0d40b25,25068,13130,2443,Stefan Bühler,2,0,2,0,0,0,0,0,0,0,0,0,0,0,1378821913,OK,2,2,1,1,0,1,1,False,13189,5352"

# Get the last line of the csv file using tail and make sure it matches the correct string
OFFLINE_LAST_LINE=$(tail -n 1 data/lighttpd2/Lighttpd2Offline.csv | sed 's/\r//g')
echo -n "#${NUM} Covrig offline test: "
if [ "${OFFLINE_LAST_LINE}" != "${OFFLINE_CORRECT_STRING}" ]; then
    echo "Failed"
    echo -e "Expected: ${OFFLINE_CORRECT_STRING}"
    echo -e "Got: ${OFFLINE_LAST_LINE}"
    exit 1
fi

# If it succeeds, then we're good
echo "Succeeded"

# Cleaning up
rm -rf data/lighttpd2
rm -rf tests/logs/test-offline.log

# All tests passed
echo "All offline tests passed"
exit 0