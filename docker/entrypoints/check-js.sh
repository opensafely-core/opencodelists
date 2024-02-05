#!/bin/bash

set -euo pipefail

npx prettier . --check

echo Running eslint
npx eslint assets/src/scripts/builder/* assets/src/scripts/hierarchy.js
