#!/bin/bash

# Bash strict mode:
# -e: exit on error
# -u: undefined variables are errors
# -x: print each command as executed to stderr
# -o pipefail: fail pipelines if any command fails
# -o errtrace: propagate the ERR trap into functions, subshells, and
#              command substitutions
set -euxo pipefail -o errtrace

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
SANITISED_BACKUP_TMP="$BACKUP_DIR/$SANITISED_BACKUP_FILENAME.tmp"

# Capture all errors in this function
on_error() { # shellcheck disable=SC2329
    local exit_code=$?
    RESULT=${exit_code:-1}

    # Clean up a stale tmp on failure
    [ -n "${SANITISED_BACKUP_TMP:-}" ] && rm -f "$SANITISED_BACKUP_TMP" 2>/dev/null || true

    # Avoid exiting inside the handler on failures of sentry call
    set +e
    echo "Backup failed with exit code $RESULT" >&2

    # best-effort Sentry error reporting; do not cause further exit if it fails
    sentry_cron_error "$SENTRY_CRON_URL" || true
    exit "$RESULT"
}
trap on_error ERR

# Verify SQLite file passes an integrity check
verify_sqlite_integrity() {
    local file="$1"

    # Use sqlite3 CLI to run integrity_check.
    # Expect single line 'ok'
    if ! sqlite3 "$file" "PRAGMA integrity_check;" | grep -qx "ok"; then
        echo "integrity_check failed for $file" >&2
        return 1
    fi

    return 0
}

# Log start of backup in a way that won't fail the whole script if Sentry down
sentry_cron_start "$SENTRY_CRON_URL" "$CRONTAB" || true

# Make the backup dir if it doesn't exist.
mkdir "$BACKUP_DIR" -p

# Take a datestamped backup.
sqlite3 "$DATABASE_DIR/db.sqlite3" ".backup $BACKUP_FILEPATH"

# Make a sanitised copy of the backup, by copying raw backup to a tmp
# backup, and then running sanitiser on the tmp file
cp --preserve=mode,timestamps "$BACKUP_FILEPATH" "$SANITISED_BACKUP_TMP"

# Run sanitisation on the tmp file
python "$SCRIPT_DIR/sanitise_backup.py" "$SANITISED_BACKUP_TMP"

# After sanitisation, verify the integrity of the SQLite DB
verify_sqlite_integrity "$SANITISED_BACKUP_TMP"

# Move tmp in to final sanitised path
mv -f "$SANITISED_BACKUP_TMP" "$SANITISED_BACKUP_FILEPATH"

# Compress the latest backups.
# Zstandard is a fast, modern, lossless data compression algorithm.  It gives
# marginally better compression ratios than gzip on the backup and much faster
# compression and particularly decompression.  We want the backup process to be
# quick as it's a CPU-intensive activity that could affect site performance.
#
# We're going to compress both backups, but not remove originals until
# compressed files have been verified.
# Make sure that -f is used to force an overwrite of any backup that already
# exists with today's date.
zstd -q -f "$BACKUP_FILEPATH" -o "${BACKUP_FILEPATH}.zst"
zstd -q -f "$SANITISED_BACKUP_FILEPATH" -o "${SANITISED_BACKUP_FILEPATH}.zst"

# Only now remove the uncompressed originals
rm "$BACKUP_FILEPATH" "$SANITISED_BACKUP_FILEPATH"

# Symlink to the new latest backups to make it easy to discover.
# Make the target a relative path -- an absolute one won't mean the same thing
# in the host file system if executed inside a container as we expect.

# Ensure target files exist before linking
if [ -f "${BACKUP_FILEPATH}.zst" ]; then
    ln -sf "$BACKUP_FILENAME.zst" "$BACKUP_DIR/latest-db.sqlite3.zst"
else
    echo "expected compressed raw backup missing: ${BACKUP_FILEPATH}.zst" >&2
    exit 4
fi

if [ -f "${SANITISED_BACKUP_FILEPATH}.zst" ]; then
    ln -sf "$SANITISED_BACKUP_FILENAME.zst" "$BACKUP_DIR/sanitised-latest-db.sqlite3.zst"
else
    echo "expected compressed sanitised backup missing: ${SANITISED_BACKUP_FILEPATH}.zst" >&2
    exit 5
fi

# Keep only the last 14 days of raw backups.
find "$BACKUP_DIR" -name "*-db.sqlite3.zst" -type f -mtime +14 -delete

# Keep only the most recent sanitised backup.
find "$BACKUP_DIR" -name "*sanitised*-db.sqlite3.zst" ! -wholename "$SANITISED_BACKUP_FILEPATH.zst" -type f -delete

# If we've reached this point, send ok to Sentry cron monitoring
sentry_cron_ok "$SENTRY_CRON_URL"
