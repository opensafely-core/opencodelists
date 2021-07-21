#!/bin/bash

set -euo pipefail

REPO_ROOT=$(dirname "$(dirname "$(dirname "$0")")")
BACKUP_PATH="/mnt/volume-lon1-01/opencodelists-backups/core-data-$(date +%F).json.gz"

"$REPO_ROOT"/with_environment.sh \
        python \
        "$REPO_ROOT"/manage.py \
        dumpdata \
        builder codelists opencodelists \
        --indent 2 \
        --verbosity 0 \
        --output "$BACKUP_PATH"

# Keep only the last 30 backups
find "$BACKUP_PATH" -name "core-data-*.json.gz" | sort | head -n -30 | xargs rm
