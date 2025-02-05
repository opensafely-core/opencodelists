#!/bin/bash

CRONTAB_PATTERN="([\*\d+] ?)+"

function extract_crontab() {
    JOB_IDENTIFIER="$1"
    CRONTAB_SOURCE="$2"
    # the crontab schedule is on the line after the command in app.json
    # and on the same line in the cronfile
    if [[ "$CRONTAB_SOURCE" == *json ]];
    then
        LINES_AFTER_MATCH=2
    else
        LINES_AFTER_MATCH=0
        # ensure we only match the terminal argument
        JOB_IDENTIFIER=" $JOB_IDENTIFIER\$"
    fi
    CRONTAB=$(grep -A "$LINES_AFTER_MATCH" "$JOB_IDENTIFIER" "$CRONTAB_SOURCE" | grep -oP "$CRONTAB_PATTERN" | sed -e "s/ $//")
    echo "$CRONTAB"
}

# Sentry DSN as used in other bits of Sentry monitoring in this project
# is not the same as the API endpoint for Cron Monitoring.
# This function modifies it such that it looks like what's described
# at https://docs.sentry.io/product/crons/getting-started/http/
function sentry_cron_url() {
    SENTRY_DSN="$1"
    JOB_NAME="$2"

    # dots not supported in job names, replace with underscores
    JOB_NAME="${JOB_NAME//\./_}"

    # modify the DSN to point it at the cron API
    SENTRY_CRON_URL=$(sed -E "s/([0-9]+$)/api\/\1/g" <<< "$SENTRY_DSN")
    echo "$SENTRY_CRON_URL/cron/$JOB_NAME"
}

function sentry_cron_start() {
    SENTRY_CRON_URL="$1"
    CRONTAB="$2"
    MONITOR_CONFIG=$(printf '{
        "monitor_config": {
            "schedule":{
                "type":"crontab",
                "value": "%s"
                },
            "checkin_margin":"5",
            "max_runtime":"300"
            },
        "status":"in_progress"
        }' "$CRONTAB")
    curl -X POST "$SENTRY_CRON_URL" \
        --header 'Content-Type: application/json' \
        --data-raw "$MONITOR_CONFIG"
}

function sentry_cron_ok() {
    SENTRY_CRON_URL="$1"
    curl "$SENTRY_CRON_URL?status=ok"
}

function sentry_cron_error() {
    SENTRY_CRON_URL="$1"
    curl "$SENTRY_CRON_URL?status=error"
}
