#!/bin/bash

declare -a cmds=(
    # "black ."
    "isort --recursive --skip migrations ."
)

for cmd in "${cmds[@]}"; do
  echo "$cmd"
  eval "$cmd"
done
