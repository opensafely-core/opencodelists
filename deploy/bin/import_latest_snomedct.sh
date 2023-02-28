#!/bin/bash

set -euo pipefail

# NOTE: this script is run by cron (as the dokku user) every Tuesday

# Updates to coding systems require restarting the dokku app, so this job is
# not dokku-managed

# This script should be copied to /var/lib/dokku/data/storage/opencodelists/import_latest_snomedct.sh
# on dokku3 and run using the cronfile at opencodelists/deploy/bin/import_latest_snomedct_cron
# SLACK_WEBHOOK_URL is an environment variable set in the cronfile on dokku3

REPO_ROOT="/app"
DOWNLOAD_DIR="/storage/data/snomedct"


#  Post starting import message to slack
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Starting OpenCodelists import of latest snomedct release"}'\
    "${SLACK_WEBHOOK_URL}"


/usr/bin/dokku run opencodelists \
    python "$REPO_ROOT"/manage.py import_latest_data snomedct "${DOWNLOAD_DIR}" \
    && /usr/bin/dokku ps:restart opencodelists

RESULT=$?

if [ $RESULT == 0 ] ; then
  #  Post success message to slack
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Latest snomedct release successfully imported to OpenCodelists"}'\
    "${SLACK_WEBHOOK_URL}"
else
  #  Post failure message to slack
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Latest snomedct release failed to import to OpenCodelists; this is probably because no new release was found."}'\
    "${SLACK_WEBHOOK_URL}"
fi
