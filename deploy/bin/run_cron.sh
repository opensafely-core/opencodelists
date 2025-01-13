#!/bin/bash

set -euo pipefail

CRONTAB_PATTERN="([\*\d]+ )+"

JOB_NAME="$1"
if ! test -z "$2";
then
    JOB_ARG="$2"
fi


function sentry_cron_start() {
    SENTRY_CRON_URL="$1"
    CRONTAB="$2"
    curl -X POST "$SENTRY_CRON_URL" \
        --header 'Content-Type: application/json' \
        --data-raw "{\"monitor_config\": {\"schedule\": {\"type\": \"crontab\", \"value\": \"$CRONTAB\"}}, \"status\": \"in_progress\"}"
}
function sentry_cron_ok() {
    SENTRY_CRON_URL="$1"
    curl "$SENTRY_CRON_URL?status=ok"
}
function sentry_cron_error() {
    SENTRY_CRON_URL="$1"
    curl "$SENTRY_CRON_URL?status=error"
}
function sentry_cron_url() {
    SENTRY_DSN="$1"
    JOB_NAME="$2"
    # modify the DSN to point it at the cron API
    SENTRY_CRON_URL=$(sed -E "s/([0-9]+$)/api\/\1/g" <<< "$SENTRY_DSN")
    echo "$SENTRY_CRON_URL/cron/$JOB_NAME"
}


# detect is "self-managed" or "dokku-managed" cron job
# by working out if we're in or outside the container
CONTAINER_STORAGE_ROOT="/var/lib/dokku/data/storage/opencodelists"
if test -d "$CONTAINER_STORAGE_ROOT";
then
    # running outside container
    SENTRY_DSN=$(dokku config:get opencodelists SENTRY_DSN)
    # combine job name and arg for reporting to Sentry
    MONITOR_NAME="${JOB_NAME}_$JOB_ARG"
    SENTRY_CRON_URL=$(sentry_cron_url "$SENTRY_DSN $MONITOR_NAME")
    BIN_DIR="$CONTAINER_STORAGE_ROOT/deploy/bin/"
    if test -d "$BIN_DIR";
    then
        BIN_PATH="$BIN_DIR$JOB_NAME $JOB_ARG"
        CRONTAB=$(grep "$BIN_PATH" "$BIN_DIR/cronfile" | grep -oP "$CRONTAB_PATTERN")
    else
        sentry_cron_error "$SENTRY_CRON_URL"
        >&2 echo "deploy/bin not deployed to $BIN_DIR"
        exit 1
    fi
else
    # running inside container
    # sentry_dsn env var is available inside container
    SENTRY_CRON_URL=$(sentry_cron_url "$SENTRY_DSN")
    BIN_DIR="/app/deploy/bin"
    if test -d "$BIN_DIR";
    then
        CRONTAB=$(grep -A 2 "$BIN_DIR/run_cron.sh $JOB_NAME" "/app/app.json" | grep -oP "$CRONTAB_PATTERN")
        BIN_PATH+="$BIN_DIR/$JOB_NAME"
    else
        sentry_cron_error "$SENTRY_CRON_URL"
        >&2 echo "/app/deploy/bin not found"
        exit 1
    fi
fi

sentry_cron_start "$SENTRY_CRON_URL" "$CRONTAB"
RESULT=0
$BIN_PATH || RESULT=$?;
if [ $RESULT == 0  ];
then
    sentry_cron_ok "$SENTRY_CRON_URL"
else
    sentry_cron_error "$SENTRY_CRON_URL"
fi
