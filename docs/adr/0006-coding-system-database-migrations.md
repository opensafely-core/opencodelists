# ADR: Procedure for changing coding system database models and their migrations

Date: 2026-07

## Status

Accepted

## Context

Data storage for coding systems is on the basis of one sqlite database per release.
Connections for each of the databases are added to the top-level Django project
database configuration at start-up using `update_coding_system_database_connections()`.

Changes to model classes are reflected in their corresponding database tables using Django migrations.
Two management commands are used to do the most common migration operations:
* ascertaining what needs to change in a database : `makemigrations`
* applying those changes to a database: `migrate`

The `migrate` management command is called routinely as part of our build/CI/deploy
processes to ensure the database schema is coherent with the python codebase at app startup.

The `migrate` and `makemigrations` commands are unaware of the additional coding system
release databases discussed above,
and so by default only operate on the core database (everything but the coding system releases).

There exist empty tables corresponding to the coding system models in the core database -
these are a something of a vestige of a prior codebase where we did not store multiple releases of a coding system.
Luckily, these provide a reference database schema for `makemigrations`
so any calculated changes following a model class change will be accurate.

Unfortunately, this means that calling the `migrate` management command will
only apply these changes to the tables in the core database,
and will leave the coding system release databases untouched.

This results in errors when Django tries to connect to these coding system release
databases following a coding system model change and finds that the database schema is not as expected.

The `migrate` command has a `--database` argument, which allows the database connection for the migration operations to be specified.
However, this requires that the coding system database connections have been updated to work correctly,
and so ad-hoc calling of it from a command prompt may not work as expected.

Thankfully changes to coding system models are quite rare.

## Decision

- We will create a new management command dedicated to applying migrations to coding system release databases after a coding system model change
- This command will call `update_coding_system_database_connections` and then `migrate` with each available database passed as the `--database` argument
- This management command will be located in, and dedicated to the ICD-10 coding system for the time being as this is the only coding system which has had model changes and thus allows thorough testing of its functionality
  - Future changes to other coding system models will require this to be changed and tested in the coding system in question
- We will not integrate this command into our automated build/CI/deploy processes due to the rarity of such changes


## Consequences

- Deployment of changes to coding system models will require manual execution of this management command on production systems
- Developers will need to download fresh copies of all coding system release databases affected by model changes, or run this management command on their machines


## Changes
 - `coding_systems/icd10/management/commands/apply_migrations_to_all_databases.py` : Management command to apply migrations to ICD-10 coding system release databases
