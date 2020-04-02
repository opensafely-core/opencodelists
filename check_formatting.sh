#!/bin/bash

declare -a cmds=(
    # "black --check ."
    "flake8"
    "isort --check-only --recursive ."
)

for cmd in "${cmds[@]}"; do
  echo "$cmd"
  eval "$cmd" || exit 1
done
