#!/bin/bash

set -euo pipefail

echo Running black
black --check .
echo Running isort
isort --check-only --diff .
echo Running flake8
flake8
