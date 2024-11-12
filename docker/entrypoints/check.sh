#!/bin/bash

set -euo pipefail

echo Running ruff formatting check
ruff format --check .
echo Running ruff linting check
ruff check .
