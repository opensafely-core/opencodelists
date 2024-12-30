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
BINPATH="/var/lib/dokku/data/storage/opencodelists/"
if test -d "$BINPATH";
then
    # running outside container
    BIN_PATH+="deploy/bin/"
    if test -d "$BINPATH";
    then
        CRONFILE="$BIN_PATH"${JOB_NAME//".sh"/"_"}"${JOB_ARG}_cronfile"
        CRONTAB=$(grep -oP "$CRONTAB_PATTERN" "$CRONFILE")

        BIN_PATH+="$JOB_NAME $JOB_ARG"
        
        SENTRY_DSN=$(dokku config:get opencodelists SENTRY_DSN)
        
        # combine job name and arg for reporting to Sentry
        JOB_NAME+="_$JOB_ARG"
    else
        echo "deploy/bin not deployed"
        exit 1
    fi
else
    # running inside container
    BIN_PATH="/app/deploy/bin"
    CRONTAB=$(grep -A 2 "$BIN_PATH/run_cron.sh $JOB_NAME" "/app/app.json" | grep -oP "$CRONTAB_PATTERN")
    BIN_PATH+="/$JOB_NAME"
    # sentry_dsn env var is available inside container
fi

# modify the DSN to point it at the cron API
SENTRY_CRONS=$(sed -E "s/([0-9]+$)/api\/\1/g" <<< "$SENTRY_DSN")
SENTRY_CRONS+="/cron/$JOB_NAME"

function sentry_cron_start() {
curl -X POST "${SENTRY_CRONS}" \
    --header 'Content-Type: application/json' \
    --data-raw "{\"monitor_config\": {\"schedule\": {\"type\": \"crontab\", \"value\": \"$CRONTAB\"}}, \"status\": \"in_progress\"}"
}
function sentry_cron_ok() {
    curl "${SENTRY_CRONS}?status=ok"
}
function sentry_cron_error() {
    curl "${SENTRY_CRONS}?status=error"
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
