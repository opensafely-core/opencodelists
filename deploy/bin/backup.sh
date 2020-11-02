#!/bin/bash

set -euo pipefail

REPO_ROOT=$(dirname "$(dirname "$(dirname "$0")")")
BACKUP_PATH="/mnt/volume-lon1-01/opencodelists-backups/core-data-$(date +%F).json"

"$REPO_ROOT"/with_environment.sh \
        python \
        "$REPO_ROOT"/manage.py \
        dumpdata \
        builder codelists opencodelists \
        --indent 2 \
        --verbosity 0 \
        --output "$BACKUP_PATH"
