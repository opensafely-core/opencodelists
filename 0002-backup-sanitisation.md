# Backup Sanitisation

Date: 2024-03

## Status

Accepted

## Context

OpenCodelists stores various data that could be considered Personal Data under the GDPR.
These data are backed up as part of the routine backup process.

Developers regularly use these backups as development data, copying them to their local machine.
This copying carries a risk of personal data from OpenCodelists leaking elsewhere.

For this reason, and in order to satisfy our obligations under the GDPR, we must take reasonable
measure to avoid transfer of Personal Data outside of secure storage.

The OpenCodelists data model is quite complex and a coherent and realistic dataset is necessary for development.
For debugging user-reported issues, as near to a full copy of the production dataset is necessary.

Generating development datasets has been investigated,
as has co-opting OpenCodelists' test fixture data for development purposes.
Both were found to be either inadequate or infeasible.

## Decision

We will "sanitise" a copy of the OpenCodelists backup by
removing Personal Data/PII wherever possible.
This will include both fields that explicitly contain personal data (e.g. names, email addresses)
and user-provided freetext data that could conceivably contain personal data.

We will retain only one copy of this backup, in contrast to the 30d retention of the full backups.

We will direct developers to use the "sanitised" backup in lieu of the full backups.

## Consequences

We will reduce the risk of personal data leakage via developers copying full backups.

If a point-in-time backup other than the most recent is needed for debugging,
this will need to be manually sanitised before use.

Direct identification of users, and by extension their codelists, will not be possible
in the sanitised dataset which may hinder investigation of user queries and issues.
