#!/bin/bash

set -euo pipefail

CRONTAB_PATTERN="([\*\d]+ )+"

JOB_NAME="$1"
if ! test -z "$2";
then
    JOB_ARG="$2"
fi

# detect is "self-managed" or "dokku-managed" cron job
# by working out if we're in or outside the container
CONTAINER_STORAGE_ROOT="/var/lib/dokku/data/storage/opencodelists"
if test -d "$CONTAINER_STORAGE_ROOT";
then
    # running outside container
    BIN_DIR="$CONTAINER_STORAGE_ROOT/deploy/bin/"
    if test -d "$BIN_DIR";
    then
        CRONFILE="$BIN_DIR${JOB_NAME//"_release.sh"/"_"}${JOB_ARG}_cronfile"
        CRONTAB=$(grep -oP "$CRONTAB_PATTERN" "$CRONFILE")

        BIN_PATH="$BIN_DIR$JOB_NAME $JOB_ARG"

        SENTRY_DSN=$(dokku config:get opencodelists SENTRY_DSN)

        # combine job name and arg for reporting to Sentry
        JOB_NAME+="_$JOB_ARG"
    else
        echo "deploy/bin not deployed"
        exit 1
    fi
else
    # running inside container
    BIN_PATH="/app/deploy/bin/$JOB_NAME.sh"
    CRONTAB=$(grep -A 2 "$JOB_NAME" "/app/app.json" | grep -oP "$CRONTAB_PATTERN")
    # sentry_dsn env var is available inside container
fi

# modify the DSN to point it at the cron API
SENTRY_CRON_URL=$(sed -E "s/([0-9]+$)/api\/\1/g" <<< "$SENTRY_DSN")
SENTRY_CRON_URL+="/cron/$JOB_NAME"

function sentry_cron_start() {
curl -X POST "${SENTRY_CRON_URL}" \
    --header 'Content-Type: application/json' \
    --data-raw "{\"monitor_config\": {\"schedule\": {\"type\": \"crontab\", \"value\": \"$CRONTAB\"}}, \"status\": \"in_progress\"}"
}
function sentry_cron_ok() {
    curl "${SENTRY_CRON_URL}?status=ok"
}
function sentry_cron_error() {
    curl "${SENTRY_CRON_URL}?status=error"
}

sentry_cron_start
RESULT=0
$BIN_PATH || RESULT=$?;
if [ $RESULT == 0  ];
then
    sentry_cron_ok
else
    sentry_cron_error
fi
