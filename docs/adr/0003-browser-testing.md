# Automated browser testing

Date: 2025-05

## Status

Draft

## Context

While we have unit tests for parts of our code, both frontend and
backend, user flows throughout the application end-to-end, integrating
these are not tested.

It would be useful to have such tests to validate that key user journeys
continue to function as expected.

## Decision

We will add automated browser tests that are run using Playwright and
pytest-django's `live_server` fixture.

We will use the existing `universe` fixtures for the time being to setup
the coding system data where appropriate, rather than reimplementing
those. It is possible that the existing test fixture system is redesigned in
future to simplify it, and that simplification may help setup of these
tests.

These tests will be run separately from the existing unit tests. This is
partly a design choice — to keep the existing test suite fast — and
partly a consequence of the fixture setup — pytest-django's
`live_server` fixture resets database state between tests.

## Consequences

The tests will need to be maintained, and new tests added if we add
other important user journeys.

If the fixture setup for testing is changed, we will have to adapt our
tests accordingly.
