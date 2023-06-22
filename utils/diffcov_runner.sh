# Short script to set up vars for and run diffcov.sh over a series of repos.

DIFF_CMDS=(
    "apr remotedata/apr/coverage 3b87c3b 99fffba"
#    "binutils remotedata/binutils/coverage 0302afd 2b9ed0a binutils"
    "binutils-gdb remotedata/binutils-gdb/coverage 781303c 28ab94f binutils"
    "curl remotedata/curl/coverage 8026bd7 abff183"
    "git remotedata/git/coverage 001d116 ba928e9"
    "lighttpd2 remotedata/lighttpd2/coverage ce4f939 1058654 src"
    "memcached remotedata/memcached/coverage d9220d6 7d6907e"
    "redis remotedata/redis/coverage 011fa89 4208666 src"
    "vim remotedata/vim/coverage 9d182dd 763209c src"
    "zeromq remotedata/zeromq/coverage 36bfaaa d82117f src"
)

# Running instructions:
# 1. Clone the repos to be tested into remotedata/
# 2. Run this script from the root of the repo

# For each repo, run diffcov.sh by running ./utils/diffcov.sh DIFF_CMDS[i]

for cmd in "${DIFF_CMDS[@]}"; do
    set -- $cmd
    repo=$1
    coverage_dir=$2
    start=$3
    end=$4
    source_dir=$5
    echo "Running diffcov.sh for $repo"
    ./utils/diffcov.sh $repo $coverage_dir $start $end $source_dir
done

for cmd in "${DIFF_CMDS[@]}"; do
    set -- $cmd
    repo=$1

    # Now run python3 utils/diffcov_to_csv.py diffcov/genhtml_output_apr.txt diffcov/diffcov_apr.csv
    echo "Converting diffcov output to csv for $repo"
    python3 utils/diffcov_to_csv.py diffcov/genhtml_output_$repo.txt diffcov/diffcov_$repo.csv

done

# Copy each file to remotedata/$repo/diffcov_$repo.csv
for cmd in "${DIFF_CMDS[@]}"; do
    set -- $cmd
    repo=$1
    cp diffcov/diffcov_$repo.csv remotedata/$repo/diffcov_$repo.csv
    if [ $? -eq 0 ]; then
        echo "Copied diffcov_$repo.csv to remotedata/$repo/diffcov_$repo.csv"
    else
        echo "Failed to copy diffcov_$repo.csv to remotedata/$repo/diffcov_$repo.csv"
    fi
done

# Sum the two binutils files
#python3 utils/sum_diffcovs.py remotedata/binutils-binutils-gdb-combined/diffcov_binutils_combined.csv remotedata/binutils/diffcov_binutils.csv remotedata/binutils-gdb/diffcov_binutils-gdb.csv