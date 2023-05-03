#!/bin/bash

# Example, build zeromq:
# ./docker_build.sh zeromq zeromq4-x
# ./docker_build.sh redis

# if no args supplied, show usage
if [ $# -eq 0 ]; then
  echo "Usage: $0 <repo> [dir]"
  exit 1
fi

REPO=$1
DIR=$2
# If there is no second argument, DIR = REPO
if [ -z "$DIR" ]; then
  DIR=$REPO
fi

docker build -t --nocache "$REPO" -f containers/"$DIR"/Dockerfile containers/"$DIR"
echo "Built ${REPO}"
echo "==============="