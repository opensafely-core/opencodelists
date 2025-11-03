#!/bin/bash

set -euxo pipefail

# import sentry functions (must be in same dir as this script)
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/sentry_cron_functions.sh"

# set up sentry monitoring
SENTRY_MONITOR_NAME=$(basename "$0")
CRONTAB=$(extract_crontab "$SENTRY_MONITOR_NAME" "/app/app.json")
SENTRY_CRON_URL=$(sentry_cron_url "$SENTRY_DSN" "$SENTRY_MONITOR_NAME")

# DATABASE_DIR is configured via dokku (see DEPLOY.md)
BACKUP_DIR="$DATABASE_DIR/backup/db"
BACKUP_FILENAME="$(date +%F)-db.sqlite3"
BACKUP_FILEPATH="$BACKUP_DIR/$BACKUP_FILENAME"
SANITISED_BACKUP_FILENAME="sanitised-$BACKUP_FILENAME"
SANITISED_BACKUP_FILEPATH="$BACKUP_DIR/$SANITISED_BACKUP_FILENAME"

function run_backup() {
    # Make the backup dir if it doesn't exist.
    mkdir "$BACKUP_DIR" -p

    # Take a datestamped backup.
    sqlite3 "$DATABASE_DIR/db.sqlite3" ".backup $BACKUP_FILEPATH"

    # Make a sanitised copy of the backup.
    cp "$BACKUP_FILEPATH" "$SANITISED_BACKUP_FILEPATH"
    python "$SCRIPT_DIR/sanitise_backup.py" "$SANITISED_BACKUP_FILEPATH"

    # Compress the latest backups.
    # Zstandard is a fast, modern, lossless data compression algorithm.  It gives
    # marginally better compression ratios than gzip on the backup and much faster
    # compression and particularly decompression.  We want the backup process to be
    # quick as it's a CPU-intensive activity that could affect site performance.
    # --rm flag removes the source file after compression.
    zstd "$BACKUP_FILEPATH" --rm
    zstd "$SANITISED_BACKUP_FILEPATH" --rm

    # Symlink to the new latest backups to make it easy to discover.
    # Make the target a relative path -- an absolute one won't mean the same thing
    # in the host file system if executed inside a container as we expect.
    ln -sf "$BACKUP_FILENAME.zst" "$BACKUP_DIR/latest-db.sqlite3.zst"
    ln -sf "$SANITISED_BACKUP_FILENAME.zst" "$BACKUP_DIR/sanitised-latest-db.sqlite3.zst"

    # Keep only the last 14 days of raw backups.
    find "$BACKUP_DIR" -name "*-db.sqlite3.zst" -type f -mtime +14 -exec rm {} \;

    # Keep only the most recent sanitised backup.
    find "$BACKUP_DIR" -name "*sanitised*-db.sqlite3.zst" ! -wholename "$SANITISED_BACKUP_FILEPATH.zst" -type f -exec rm {} \;
}

# log start of backup in a way that won't fail the whole script if sentry down
sentry_cron_start "$SENTRY_CRON_URL" "$CRONTAB" || RESULT=$?

# run the backup
RESULT=0
run_backup || RESULT=$?

if [ $RESULT == 0 ] ; then
    sentry_cron_ok "$SENTRY_CRON_URL"
else
    sentry_cron_error "$SENTRY_CRON_URL"
fi
