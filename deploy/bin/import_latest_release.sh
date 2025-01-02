#!/bin/bash

set -euo pipefail

# NOTE: this script is run by cron (as the dokku user) weekly
# For dm+d, it is run every Monday night, to coincide with weekly
# dm+d releases
# https://isd.digital.nhs.uk/trud/users/authenticated/filters/0/categories/6/items/24/releases

# For snomedct, it is run every Tuesday. This is arbitrary; snomed releases
# are not made on a very regular schedule, and typically happen about every
# 2 months.  We run it weekly, expecting it to "fail" because it already has the
# latest release.

# Updates to coding systems require restarting the dokku app, so this job is
# not dokku-managed

# SLACK_WEBHOOK_URL and SLACK_TEAM_WEBHOOK_URL are environment variables set in the cronfile on dokku3
# General notification messages (import start, complete etc) are posted to the
# SLACK_WEBHOOK_URL channel (#tech-noise).  Failures are posted to the
# SLACK_TEAM_WEBHOOK_URL. This should be set to the channel for the team responsible
# for OpenCodelists.

CODING_SYSTEM=$1

REPO_ROOT="/app"
DOWNLOAD_DIR="/storage/data/${CODING_SYSTEM}"
# make the log dir if necessary
LOG_DIR=/var/lib/dokku/data/storage/opencodelists/coding_systems/error_logs
mkdir -p "${LOG_DIR}"

current_timestamp=$(date "+%Y.%m.%d-%H.%M.%S")
LOG_FILE="${LOG_DIR}/${CODING_SYSTEM}_import_${current_timestamp}.txt"


function post_to_slack() {
  message_text=$1
  webhook_url=$2
  message_json='{"text": "'"$message_text"'"}'
  curl -X POST -H 'Content-type: application/json' \
  --data "${message_json}" \
  "${webhook_url}"
}

function run_dokku_import_command () {
  # pipe the output via sed to remove ansi escape sequences
  /usr/bin/dokku run opencodelists \
      python "$REPO_ROOT"/manage.py \
      import_latest_data "${CODING_SYSTEM}" "${DOWNLOAD_DIR}" |& sed 's/\x1b\[[0-9;]*[mGKHF]//g' > "${LOG_FILE}"
}


function post_starting_message() {
  starting_message_text="Starting OpenCodelists import of latest ${CODING_SYSTEM}"
  post_to_slack "${starting_message_text}" "${SLACK_WEBHOOK_URL}"
}


function post_success_message_and_cleanup() {
  # restart app
  /usr/bin/dokku ps:restart opencodelists
  #  Post success message to slack
  success_message_text="Latest ${CODING_SYSTEM} release successfully imported to OpenCodelists"
  post_to_slack "${success_message_text}" "${SLACK_WEBHOOK_URL}"
  # remove log file; only persist log files for errors
  rm "${LOG_FILE}"
}


function post_failure_message_and_cleanup() {
  # restart app
  /usr/bin/dokku ps:restart opencodelists
  # Report and notify team in slack
  failure_message_text="\
Latest ${CODING_SYSTEM} release failed to import to OpenCodelists.\n \
Check logs on dokku3 at ${LOG_FILE}\n \
If you need to rerun the import, find the release name and valid from date (check the start of the log file) and run: \
 \`\`\`dokku run opencodelists \
python $REPO_ROOT/manage.py \
import_coding_system_data ${CODING_SYSTEM} ${DOWNLOAD_DIR} \
--release <release name> \
--valid-from <YYYY-MM-DD> \
--force && dokku ps:restart opencodelists\`\`\`"
  post_to_slack "${failure_message_text}" "${SLACK_TEAM_WEBHOOK_URL}"
}


function post_no_new_release_message_and_cleanup() {
  message_text="No new ${CODING_SYSTEM} release to import."
    post_to_slack "${message_text}", "${SLACK_WEBHOOK_URL}"
    # remove the log file, this wasn't an actual error.
    rm "$LOG_FILE"
}


#  Post starting import message to slack
post_starting_message

# run the command
RESULT=0
run_dokku_import_command || RESULT=$?

if [ $RESULT == 0 ] ; then
  post_success_message_and_cleanup
else
  # Check last log line to see if the command failed because no new release was found
  last_log_line=$(tail -1 "${LOG_FILE}")
  if [[ "${last_log_line}" == *"already exists for the latest release"* ]];
  then
    post_no_new_release_message_and_cleanup
  else
    post_failure_message_and_cleanup
  fi
fi
