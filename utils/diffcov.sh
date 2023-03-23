#!/bin/bash
# TODO: run this and formalize this as a proper script - atm this is just a bunch of commands that I ran to get index.html
# Run all the commands that setup up redis up until lcov

# d645757 is baseline - 347ab78 is curr

# be in root of repo

# unzip coverage data, place into tmp2 and tmp2-baseline
tar xjf data/parallel_redis/coverage-d645757.tar.bz2 -C tmp2-baseline
tar xjf data/parallel_redis/coverage-347ab78.tar.bz2 -C tmp2-current

# navigate to repos/redis
cd repos/redis

git checkout d645757
cp -R src ../tmp2-baseline/

git checkout 347ab78
cp -R src ../tmp2-current/
# use git blame to annotate the files
../../../utils/annotate_files.sh src # used to run as . from redis/src, hopefully this works
mv src/*.annotated ../../../tmp2-current/src


# do the diff between the <baseline> and the <current>
git diff d645757 347ab78 --src-prefix=tmp2-baseline/ --dst-prefix="" -- src/*.c src/*.h  > ../../tmp2-current/diff.txt

# go back to root of repo
cd ../..

# localize the coverage data info
cd tmp2-baseline
python3 utils/localize_info_src.py tmp2-baseline/total.info /home/redis $(realpath tmp2-baseline)

# back to root of repo
cd ..

cd tmp2-current
python3 utils/localize_info_src.py tmp2-current/total.info /home/redis $(realpath tmp2-current)

# while in tmp2-current, run genhtml
genhtml --branch-coverage --ignore-errors unmapped,inconsistent total.info --baseline-file ../tmp2-baseline/total.info --diff-file diff.txt --output-directory . --annotate-script ../utils/annotate.sh
