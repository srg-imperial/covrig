#!/usr/bin/env bash

# run blame.sh for all files in a directory that is not already .annotated

DIR=$1

# get location of this script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

for file in $DIR/*; do
    if [[ $file == *.annotated ]]; then
        echo "Skipping $file"
    # do for *.c, *.h, *.cpp, *.hpp
    elif [[ $file == *.c ]] || [[ $file == *.h ]] || [[ $file == *.cpp ]] || [[ $file == *.hpp ]]; then
        echo "Running blame.sh on $file"
        "$SCRIPT_DIR"/blame.sh "$file"
    fi
done