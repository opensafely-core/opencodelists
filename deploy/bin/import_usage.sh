#!/bin/bash

set -euo pipefail

# NOTE: this script is intended for self-managed cron, copied outside the
# container and run as the dokku user (see deploy/bin/cronfile and DEPLOY.md).
#
# It follows the same notification conventions as import_latest_release.sh:
# - post start/success messages to SLACK_WEBHOOK_URL
# - post failures to SLACK_TEAM_WEBHOOK_URL
# - report start/ok/error to Sentry Cron Monitoring

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/sentry_cron_functions.sh"

SCRIPT_NAME=$(basename "$0")
CODING_SYSTEM=$1

SENTRY_MONITOR_NAME="${SCRIPT_NAME}_${CODING_SYSTEM}"
SENTRY_DSN=$(dokku config:get opencodelists SENTRY_DSN)
CRONTAB=$(extract_crontab "import_usage.sh $CODING_SYSTEM" "$SCRIPT_DIR/cronfile")
SENTRY_CRON_URL=$(sentry_cron_url "$SENTRY_DSN" "$SENTRY_MONITOR_NAME")

REPO_ROOT="/app"
LOG_DIR=/var/lib/dokku/data/storage/opencodelists/usage_logs
mkdir -p "$LOG_DIR"

current_timestamp=$(date "+%Y.%m.%d-%H.%M.%S")
LOG_FILE="$LOG_DIR/import_usage_${CODING_SYSTEM}_${current_timestamp}.txt"


function post_to_slack() {
  message_text=$1
  webhook_url=$2
  message_json='{"text": "'"$message_text"'"}'
  curl -X POST -H 'Content-type: application/json' \
  --data "$message_json" \
  "$webhook_url"
}


function run_import_command() {
  /usr/bin/dokku run opencodelists \
      python "$REPO_ROOT"/manage.py import_usage --coding-system "$CODING_SYSTEM" |& \
      sed 's/\x1b\[[0-9;]*[mGKHF]//g' > "$LOG_FILE"
}


function post_starting_message() {
  message_text="Starting OpenCodelists ${CODING_SYSTEM} usage import"
  post_to_slack "$message_text" "$SLACK_WEBHOOK_URL"
  sentry_cron_start "$SENTRY_CRON_URL" "$CRONTAB"
}


function post_success_message_and_cleanup() {
  message_text="OpenCodelists ${CODING_SYSTEM} usage import completed successfully"
  post_to_slack "$message_text" "$SLACK_WEBHOOK_URL"
  rm "$LOG_FILE"
  sentry_cron_ok "$SENTRY_CRON_URL"
}


function post_failure_message() {
  message_text="\
OpenCodelists ${CODING_SYSTEM} usage import failed.\n \
Check logs on dokku3 at $LOG_FILE\n \
If you need to rerun manually, use: \
\`\`\`dokku run opencodelists python $REPO_ROOT/manage.py import_usage --coding-system $CODING_SYSTEM\`\`\`"
  post_to_slack "$message_text" "$SLACK_TEAM_WEBHOOK_URL"
  sentry_cron_error "$SENTRY_CRON_URL"
}


post_starting_message

RESULT=0
run_import_command || RESULT=$?

if [ "$RESULT" -eq 0 ] ; then
  post_success_message_and_cleanup
else
  post_failure_message
fi

exit "$RESULT"
