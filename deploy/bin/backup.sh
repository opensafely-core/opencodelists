#!/bin/bash

set -euxo pipefail

# We are changing the backup format and where they are stored. We want to
# retain 30 days of backups across both locations and formats. Once there
# are none of the old format remaining, this can be updated to just refer
# to the new location.
REPO_ROOT="/app"
ORIGINAL_BACKUP_DIR="/storage"
BACKUP_DIR="$ORIGINAL_BACKUP_DIR/backup/db"

# Make the backup dir if it doesn't exist.
mkdir "$BACKUP_DIR" -p

# Take a datestamped backup.
BACKUP_FILENAME="$BACKUP_DIR/$(date +%F)-db.sqlite3"
sqlite3 "$REPO_ROOT/db.sqlite3" ".backup $BACKUP_FILENAME"

# Compress the latest backup.
gzip -f "$BACKUP_FILENAME"

# Symlink to the new latest backup to make it easy to discover.
ln -sf "$BACKUP_FILENAME.gz" "$BACKUP_DIR/latest-db.sqlite3.gz"

# Keep only the last 30 days of backups.
# For now, apply this to both the original backup dir with backups based on the
# Django dumpdata management command and the new dir with backups based on
# sqlite .backup. Once there are none of the former remaining, the first line can be
# removed, along with most of this comment.
find "$ORIGINAL_BACKUP_DIR" -name "core-data-*.json.gz" -type f -mtime +30 -exec rm {} \;
find "$BACKUP_DIR" -name "*-db.sqlite3.gz" -type f -mtime +30 -exec rm {} \;
