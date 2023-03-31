#!/bin/bash

set -euo pipefail

echo Running black
black --check .
echo Running ruff
ruff check .
