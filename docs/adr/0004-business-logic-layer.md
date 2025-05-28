# `actions.py` business logic layer

Date: 2025-05

## Status

Draft

## Context

A Django project uses a model-view-template architecture where models represent
the data layer, templates the presentation layer, and views process and respond
to HTTP requests by retrieving data and passing it to templates.

Business logic that modifies state or performs actions can be represented in
the models or views but when complex this mixes concerns and can lead to
inconsistent approaches, duplication, and leave code harder to read, reason
about, maintain, and test.

OpenCodelists represents users, organisations, codelists, codelist versions,
search data, review status, and other codelist metadata with Django model
instances in its core database.

## Decision

- We place business logic in a module called `actions.py` in each app that
  affects state: the `builder`, `codelists`, and `opencodelists` apps.
- Code for views, tests, and management commands in those apps should not
  invoke create, update, or delete operations on Django models directly but
  instead via functions imported from `actions.py` modules.
- Model or manager methods are permitted where they don't involve complex
  interactions with other models or significant side effects.
- For now, each `actions.py` will be a flat module. If complexity grows, we can
  refactor into an `actions/` directory with submodules for logical grouping.
- The above points do not apply to other apps or the coding systems databases
  (we don't expect those to change at all once imported).
- This approach is enforced by convention.

## Consequences

- Enhanced developer experience, improved code that is more reusable, testable, and
maintainable.
- Developers will need to be aware of this convention and follow it when
  writing and reviewing code.
