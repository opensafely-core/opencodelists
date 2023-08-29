#!/bin/bash

set -euo pipefail

# NOTE: this script is run by cron (as the dokku user) every Monday, to co-incide with weekly
# dm+d releases
# https://isd.digital.nhs.uk/trud/users/authenticated/filters/0/categories/6/items/24/releases

# Updates to coding systems require restarting the dokku app, so this job is
# not dokku-managed

# This script should be copied to /var/lib/dokku/data/storage/opencodelists/import_latest_dmd.sh
# on dokku3 and run using the cronfile at opencodelists/deploy/bin/import_latest_dmd_cron
# SLACK_WEBHOOK_URL is an environment variable set in the cronfile on dokku3

REPO_ROOT="/app"
DOWNLOAD_DIR="/storage/data/dmd"


#  Post starting import message to slack
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Starting OpenCodelists import of latest dm+d release"}'\
    "${SLACK_WEBHOOK_URL}"


/usr/bin/dokku run opencodelists \
    python "$REPO_ROOT"/manage.py import_latest_data dmd "${DOWNLOAD_DIR}" \
    && /usr/bin/dokku ps:restart opencodelists

RESULT=$?

if [ $RESULT == 0 ] ; then
  #  Post success message to slack
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Latest dm+d release successfully imported to OpenCodelists"}'\
    "${SLACK_WEBHOOK_URL}"
else
  #  Post failure message to slack
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Latest dm+d release failed to import to OpenCodelists. Calling tech-support."}'\
    "${SLACK_WEBHOOK_URL}"
fi
