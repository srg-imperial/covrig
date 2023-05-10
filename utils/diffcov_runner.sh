# Short script to set up vars for and run diffcov.sh over a series of repos.

# Set up vars
#repos = {
#    'apr': {'start': '886b908', 'end': '8fb7fa4', 'source_dir': None},
#    'binutils': {'start': '0302afd', 'end': '2b9ed0a', 'source_dir': 'binutils'},
#    'binutils-gdb': {'start': '20cef68', 'end': '28ab94f', 'source_dir': 'binutils'},
#    # 'curl': {'start': '#######', 'end': '#######', 'source_dir': 'curl'},
#    'git': {'start': '4d1c565', 'end': 'd7aced9', 'source_dir': None},
#    'lighttpd2': {'start': 'a3b7ce7', 'end': '1058654', 'source_dir': 'src'},
#    'memcached': {'start': '671fcca', 'end': '7d6907e', 'source_dir': None},
#    'redis': {'start': '3cbce4f', 'end': '5500c51', 'source_dir': 'src'},
#    # TODO: Will need to adjust end when adding new data from resize
#    'vim': {'start': 'e2db436', 'end': '4df7029', 'source_dir': 'src'},
#    # TODO: Adjust when data comes in with resize + coverage
#    'zeromq': {'start': 'c8e8f2a', 'end': '267699b', 'source_dir': 'src'},
#}

DIFF_CMDS=(
    "apr remotedata/apr/coverage 886b908 8fb7fa4"
    "binutils remotedata/binutils/coverage 0302afd 2b9ed0a binutils"
    "binutils-gdb remotedata/binutils-gdb/coverage 20cef68 28ab94f binutils"
    "git remotedata/git/coverage 4d1c565 d7aced9"
    "lighttpd2 remotedata/lighttpd2/coverage a3b7ce7 1058654 src"
    "memcached remotedata/memcached/coverage 671fcca 7d6907e"
    "redis remotedata/redis/coverage 3cbce4f 5500c51 src"
    "vim remotedata/vim/coverage e2db436 4df7029 src"
    "zeromq remotedata/zeromq/coverage c8e8f2a 267699b src"
)

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
python3 utils/sum_diffcovs.py remotedata/binutils-binutils-gdb-combined/diffcov_binutils_combined.csv remotedata/binutils/diffcov_binutils.csv remotedata/binutils-gdb/diffcov_binutils-gdb.csv