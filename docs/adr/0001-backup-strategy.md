# Backup strategy

Date: 2024-12

## Status

Draft

I'm proposing that we keep this in draft until backup-related issues in the
Onboarding OpenCodelists initiative are resolved or deferred. Then the outcomes
can be combined into one ADR, which will be easier to follow in future.

## Context

OpenCodelists runs on a DigitalOcean droplet with Dokku-managed docker
containers serving Django apps. There are multiple SQLite databases. The
storage file system is local. Digital Ocean offer Block and Object remote
storage solutions but we don't currently use those.

The droplet is backed up weekly, with four backups retained.

User-generated codelist content is stored in the core database along with
information on users and organizations. This is the only source of truth (SOT)
for the user-generated content, which takes some time to develop if using the
codelist builder UI. So codelist data loss is costly.

Other databases hold representations of the various coding systems and mappings
against which a codelist may be developed, displayed, and interpreted. The SOT
is the source data files provided by a third-party. These are written to once
then stored read-only. In theory, we can re-run our code against source to
re-generate the databases, reducing the cost of data loss. In practice, it may
be difficult to do this in some cases due to the original code or source data
being unavailable. Some of the source data is stored locally, but not all.

All other material required to deploy the site is under source control.

## Decision

We will back up the core database nightly using scheduled SQLite CLI commands.
The backup will be stored in the same file system. The backup will be
compressed. We will retain these backups for 30 days.

We will not back up the coding system databases other than through the
continuing weekly droplet backups.

## Consequences

The core database can be straightforwardly restored from the local nightly
backups, limiting core data loss to one day if the droplet file system is not lost.

The coding system and mapping databases can only be restored from the droplet
backups or recreated from source. Their read-only permissions partially mitigate
the risk of accidental deletion.

Restoring from the droplet backups could lead to up to a week of data loss and
it's unclear how difficult it would be to execute restoration.
