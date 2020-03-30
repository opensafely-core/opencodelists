#!/bin/bash

declare -a cmds=(
    # "black ."
    "isort --recursive **/*.py"
)

for cmd in "${cmds[@]}"; do
  echo "$cmd"
  eval "$cmd"
done
