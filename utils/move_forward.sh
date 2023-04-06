#!/bin/bash

# Move forward along master (since master is a linear history):

NUM_COMMITS=$1

git log --all --decorate --oneline | grep -B $NUM_COMMITS $(git rev-parse --short HEAD) | awk '{print $1}' | head -1 | xargs -I {} git checkout {}