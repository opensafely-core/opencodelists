#!/bin/bash

set -euo pipefail

npx prettier . --check

echo Running eslint
npx eslint static/src/js/builder/* static/src/js/hierarchy.js
