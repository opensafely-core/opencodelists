#!/bin/bash

set -euxo pipefail

# import sentry functions (must be in same dir as this script)
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/sentry_cron_functions.sh"

SENTRY_MONITOR_NAME="$0"
CRONTAB=$(extract_crontab "$SENTRY_MONITOR_NAME" "/app/app.json")
SENTRY_CRON_URL=$(sentry_cron_url "$SENTRY_DSN" "$SENTRY_MONITOR_NAME")
sentry_cron_start "$SENTRY_CRON_URL" "$CRONTAB"
{
    # DATABASE_DIR is configured via dokku (see DEPLOY.md)
    BACKUP_DIR="$DATABASE_DIR/backup/db"

    # Make the backup dir if it doesn't exist.
    mkdir "$BACKUP_DIR" -p

    # Take a datestamped backup.
    BACKUP_FILENAME="$(date +%F)-db.sqlite3"
    BACKUP_FILEPATH="$BACKUP_DIR/$BACKUP_FILENAME"
    sqlite3 "$DATABASE_DIR/db.sqlite3" ".backup $BACKUP_FILEPATH"

    # Compress the latest backup.
    # Zstandard is a fast, modern, lossless data compression algorithm.  It gives
    # marginally better compression ratios than gzip on the backup and much faster
    # compression and particularly decompression.  We want the backup process to be
    # quick as it's a CPU-intensive activity that could affect site performance.
    # --rm flag removes the source file after compression.
    zstd "$BACKUP_FILEPATH" --rm

    # Symlink to the new latest backup to make it easy to discover.
    # Make the target a relative path -- an absolute one won't mean the same thing
    # in the host file system if executed inside a container as we expect.
    ln -sf "$BACKUP_FILENAME.zst" "$BACKUP_DIR/latest-db.sqlite3.zst"

    # Keep only the last 30 days of backups.
    # For now, apply this to both the original backup dir with backups based on the
    # Django dumpdata management command and the new dir with backups based on
    # sqlite .backup. Once there are none of the former remaining, the first line can be
    # removed, along with most of this comment.
    find "$DATABASE_DIR" -name "core-data-*.json.gz" -type f -mtime +30 -exec rm {} \;
    # We initially compressed with gzip, this can be removed when none left.
    find "$BACKUP_DIR" -name "*-db.sqlite3.gz" -type f -mtime +30 -exec rm {} \;
    find "$BACKUP_DIR" -name "*-db.sqlite3.zst" -type f -mtime +30 -exec rm {} \;
    sentry_cron_ok "$SENTRY_CRON_URL"
} ||{
    sentry_cron_error "$SENTRY_CRON_URL"
}
