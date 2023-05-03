# First arg is a counter for the test number
NUM=$1

# TEST ONLINE
# ====================

# Check if repos/binutils exists
if [ ! -d repos/binutils ]; then
    echo "Failed, repos/binutils does not exist"
    exit 1
fi

# Create data/binutils directory if it doesn't exist
mkdir -p data/binutils

# Run the tests and make sure it succeeds
mkdir -p tests/logs

# Create a log file for this test named after the filename and remove the extension .sh
LOGFILE=tests/logs/"$(basename "$0" .sh)".log

echo "Building docker image for binutils..."
# Create a docker image for binutils (storage ~500MB, should take ~1min)
docker build --quiet -t binutils:12 -f containers/binutils/Dockerfile-12 containers/binutils

echo -n "#${NUM} Covrig online test: "
python3 analytics.py --output binutils --image binutils:12 --endatcommit 9d10bf2 binutils 1 &> ${LOGFILE} & pid=$!

# Draw a spinner while the tests are running
# Credit to https://stackoverflow.com/questions/12498304/using-bash-to-display-a-progress-working-indicator (William Pursell)
spin='-\|/'

i=0
while kill -0 $pid 2>/dev/null
do
  i=$(( (i+1) %4 ))
  echo -ne "#${NUM} Covrig online test: ${spin:$i:1} \033[0K\r"
  sleep .1
done

if [ $? -ne 0 ]; then
    echo "#${NUM} Covrig online test: Failed, see ${LOGFILE} for details"
    exit 1
fi

# Make sure the csv file exists
if [ ! -f data/binutils/Binutils.csv ]; then
    echo "#${NUM} Covrig online test: Failed, see ${LOGFILE} for details"
    exit 1
fi

# If it succeeds, then we're good
echo "#${NUM} Covrig online test: Succeeded"

# Update vars
NUM=$((NUM+1))

# TEST CORRECTNESS
# ====================

# Inspect the csv file and make sure it's correct
ONLINE_CORRECT_STRING="9d10bf2,25267,4138,4212,H.J. Lu,140,14,12,53.85,0,0,0,0,0,0,0,0,0,0,1282580751,OK,21,13,6,1,3,20,13,False,17589,2204"
# Note: This is the same string as for the offline test - they should be the same

# Get the last line of the csv file using tail and make sure it matches the correct string
ONLINE_LAST_LINE=$(tail -n 1 data/binutils/Binutils.csv | sed 's/\r//g')
echo -n "#${NUM} Covrig online test: "
if [ "${ONLINE_LAST_LINE}" != "${ONLINE_CORRECT_STRING}" ]; then
    # Compare all the other elements together and make sure they are the same. Start at 1
    for i in {1..31}
    do
        # Extract the the ith element of the string (beyond the ith comma)
        ONLINE_ITH_ELEMENT_CORRECT=$(echo ${ONLINE_CORRECT_STRING} | awk -F, '{print $'${i}'}')
        ONLINE_ITH_ELEMENT=$(echo ${ONLINE_LAST_LINE} | awk -F, '{print $'${i}'}')

        # Check if i is 3 or 30 or 31 (coverage or branch coverage) and convert to int
        if [ "$i" -eq 3 ] || [ "$i" -eq 30 ] || [ "$i" -eq 31 ]; then
            ONLINE_ITH_ELEMENT_CORRECT=$(echo ${ONLINE_ITH_ELEMENT_CORRECT} | awk '{print int($1)}')
            ONLINE_ITH_ELEMENT=$(echo ${ONLINE_ITH_ELEMENT} | awk '{print int($1)}')

            # Check if they are the same
            if [ "${ONLINE_ITH_ELEMENT_CORRECT}" != "${ONLINE_ITH_ELEMENT}" ]; then
              if [ "$i" -eq 3 ]; then
                echo "Warning: Coverage is not quite the same as in the testcase (this can be ok) (Expected ${ONLINE_ITH_ELEMENT_CORRECT}, got ${ONLINE_ITH_ELEMENT})"
              elif [ "$i" -eq 30 ]; then
                echo "Warning: Branch count is not quite the same as in the testcase (this can be ok) (Correct ${ONLINE_ITH_ELEMENT_CORRECT}, got ${ONLINE_ITH_ELEMENT})"
              elif [ "$i" -eq 31 ]; then
                echo "Warning: Branch coverage is not quite the same as in the testcase (this can be ok) (Correct ${ONLINE_ITH_ELEMENT_CORRECT}, got ${ONLINE_ITH_ELEMENT})"
              fi
            fi

            # Check if they are within DELTA of each other
            DELTA=5
            if [ $((ONLINE_ITH_ELEMENT_CORRECT-DELTA)) -gt ${ONLINE_ITH_ELEMENT} ] || [ $((ONLINE_ITH_ELEMENT_CORRECT+DELTA)) -lt ${ONLINE_ITH_ELEMENT} ]; then
                echo "Failed"
                echo -e "Expected: ${ONLINE_CORRECT_STRING}"
                echo -e "Got: ${ONLINE_LAST_LINE}"
                exit 1
            fi

            # Skip the rest of the loop
            continue
        fi

        # Check if they are the same (all other elements)
        if [ "${ONLINE_ITH_ELEMENT_CORRECT}" != "${ONLINE_ITH_ELEMENT}" ]; then
            echo "Failed"
            echo -e "Expected: ${ONLINE_CORRECT_STRING}"
            echo -e "Got: ${ONLINE_LAST_LINE}"
            exit 1
        fi

    done

fi

# If it succeeds, then we're good
echo "Succeeded"

# Cleaning up
rm -rf data/binutils
rm -rf tests/logs/test-online.log

# All tests passed
echo "All online tests passed"
exit 0