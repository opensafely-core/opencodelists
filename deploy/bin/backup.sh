#!/bin/bash

set -euxo pipefail

# DATABASE_DIR is configured via dokku (see DEPLOY.md)
BACKUP_DIR="$DATABASE_DIR/backup/db"

# Make the backup dir if it doesn't exist.
mkdir "$BACKUP_DIR" -p

# Take a datestamped backup.
BACKUP_FILENAME="$(date +%F)-db.sqlite3"
BACKUP_FILEPATH="$BACKUP_DIR/$BACKUP_FILENAME"
sqlite3 "$DATABASE_DIR/db.sqlite3" ".backup $BACKUP_FILEPATH"

# Compress the latest backup.
gzip -f "$BACKUP_FILEPATH"

# Symlink to the new latest backup to make it easy to discover.
# Make the target a relative path -- an absolute one won't mean the same thing
# in the host file system if executed inside a container as we expect.
ln -sf "$BACKUP_FILENAME.gz" "$BACKUP_DIR/latest-db.sqlite3.gz"

# Keep only the last 30 days of backups.
# For now, apply this to both the original backup dir with backups based on the
# Django dumpdata management command and the new dir with backups based on
# sqlite .backup. Once there are none of the former remaining, the first line can be
# removed, along with most of this comment.
find "$DATABASE_DIR" -name "core-data-*.json.gz" -type f -mtime +30 -exec rm {} \;
find "$BACKUP_DIR" -name "*-db.sqlite3.gz" -type f -mtime +30 -exec rm {} \;
