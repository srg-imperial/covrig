#!/bin/bash

for repo in "$@"
do
  docker build -t "$repo" -f containers/"$repo"/Dockerfile containers/"$repo"
  echo "Built ${repo}"
  echo "==============="
done