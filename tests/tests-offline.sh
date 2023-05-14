# First arg is a counter for the test number
NUM=$1

# TEST OFFLINE
# ====================

# Check if repos/binutils exists
if [ ! -d repos/binutils ]; then
    # Should be done by build script on GitHub Actions
    echo "Failed, repos/binutils does not exist (from git://sourceware.org/git/binutils.git)"
    exit 1
fi

# Create data/binutils directory if it doesn't exist
mkdir -p data/binutils

# Copy the coverage-9d10bf2.tar.bz2 (binutils coverage archive) to data/binutils
cp tests/data/coverage-9d10bf2.tar.bz2 data/binutils

# Run the tests and make sure it succeeds
mkdir -p tests/logs

# Create a log file for this test named after the filename and remove the extension .sh
LOGFILE=tests/logs/"$(basename "$0" .sh)".log

echo -n "#${NUM} Covrig offline test: "
python3 analytics.py --output binutils --offline --endatcommit 9d10bf2 binutils 1 &> ${LOGFILE}
if [ $? -ne 0 ]; then
    echo "Failed, see ${LOGFILE} for details"
    exit 1
fi

# Make sure the csv file exists
if [ ! -f data/binutils/BinutilsOffline.csv ]; then
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
OFFLINE_CORRECT_STRING="9d10bf2,25267,4138,4212,H.J. Lu,140,14,12,53.85,0,0,0,0,0,0,0,0,0,0,1282580751,OK,21,13,6,1,3,20,13,False,17589,2204"

# Get the last line of the csv file using tail and make sure it matches the correct string
OFFLINE_LAST_LINE=$(tail -n 1 data/binutils/BinutilsOffline.csv | sed 's/\r//g')
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
rm -rf data/binutils
rm -rf tests/logs/test-offline.log

# All tests passed
echo "All offline tests passed"
exit 0