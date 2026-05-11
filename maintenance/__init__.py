"""Maintenance migrations to fix up the production database.

This app is for maintenance migrations to fix data issues in the production
environment.  Doing these kinds of fix here rather than live in a Django shell
via SSH makes such fixes auditable, reviewable, repeatable, testable, avoids
the possibility of manual error, and fixes up development environment databases
as well. It also avoids cluttering the feature apps and getting squashed.

Make your migrations safe to apply in either production or developer
environments without the problematic data, and safe to apply repeatedly.
Probably if the fix is to remove or edit some instances, there may be no
reverse operation that can be defined.

At least manually test your migrations against a local copy of the production
database, or similar synthetic data, to get some assurance that it has the
intended effect.
"""
