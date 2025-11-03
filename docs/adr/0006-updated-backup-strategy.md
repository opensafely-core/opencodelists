# Updated backup strategy

Date: 2025-11

## Status

Approved

## Context

For the full original context of backups, see [ADR 0001: Backup strategy](docs/adr/0001-backup-strategy.md).

## Decision

This ADR proposes that we update the backup strategy to keep only the last 14 days.

Each backup we keep uses space on the internal volume of the server, and so a considered decision needs to be made to keep a backup.
We are very unlikely to restore from a backup older than a few days, due to the difference in data between the active database and the backed up databases.
For this reason, we shouldn't keep backups which we would not restore in a disaster recovery situation.

## Consequences

We will lose the opportunity to use older backups, but will gain a large amount (10GB+) of space back on the internal disk.

If, in future, we were to move backups off the main disk, we could return to keeping 30 (or more) days of backups.
