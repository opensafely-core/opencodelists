#!/bin/bash

# copy cron jobs from deploy bin directory
# to /etc/cron.d/ and populate env vars
# (must be set before running this script)

set -euo pipefail

BIN_PATH="/var/lib/dokku/data/storage/opencodelists/deploy/bin/"

for CRONFILE in "$BIN_PATH"*_cronfile; do
    DEST=$(basename "$CRONFILE")
    DEST="${DEST//_cronfile/}"
    DEST="/etc/cron.d/dokku-opencodelists-${DEST//_/-}"
    sed "s/SLACK_WEBHOOK_URL\=dummy-url/SLACK_WEBHOOK_URL\=$SLACK_WEBHOOK_URL/g" "$CRONFILE" | \
        sed "s/SLACK_TEAM_WEBHOOK_URL\=dummy-url/SLACK_TEAM_WEBHOOK_URL\=$SLACK_TEAM_WEBHOOK_URL/g" > \
        "$DEST"
done
