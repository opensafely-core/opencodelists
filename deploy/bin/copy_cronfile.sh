#!/bin/bash

# copy cron jobs from deploy bin directory to /etc/cron.d/ and populate Slack vars
# that must be set before running this script, which must be run as root

set -euo pipefail

BIN_DIR="/var/lib/dokku/data/storage/opencodelists/deploy/bin"

CRONFILE="$BIN_DIR/cronfile"
DEST="/etc/cron.d/dokku-opencodelists-cronfile"
sed "s/SLACK_WEBHOOK_URL\=dummy-url/SLACK_WEBHOOK_URL\=$SLACK_WEBHOOK_URL/g" "$CRONFILE" | \
    sed "s/SLACK_TEAM_WEBHOOK_URL\=dummy-url/SLACK_TEAM_WEBHOOK_URL\=$SLACK_TEAM_WEBHOOK_URL/g" > \
    "$DEST"
chown root:root "$DEST"
