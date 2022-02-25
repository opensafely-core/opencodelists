#!/bin/bash

set -euo pipefail

REPO_ROOT="/app"
BACKUP_DIR="/storage"

python \
"$REPO_ROOT"/manage.py \
dumpdata \
builder codelists opencodelists \
--indent 2 \
--verbosity 0 \
--output "${BACKUP_DIR}/core-data-$(date +%F).json.gz"

# Keep only the last 30 backups
find "$BACKUP_DIR" -name "core-data-*.json.gz" | sort | head -n -30 | xargs rm
