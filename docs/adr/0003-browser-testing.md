# Automated browser testing

Date: 2025-05

## Status

Accepted

## Context

We have unit tests that cover parts of our code, both frontend and backend.

However, those tests:

* do not enforce any code coverage metric, so those tests are not
  comprehensive
* only test frontend and backend in isolation; so, for example, we do
  not regularly test user flows end-to-end such as:
  * registering on the site through the signup form
  * navigating to and viewing codelists for each coding system
  * building a codelist interactively: entering searches, seeing the
    results of those searches, selecting concepts, and publishing the
    codelist

Automated web browser testing of key user journeys end-to-end would be a
useful addition. Browser testing enables us to validate that those user
journeys continue to function as intended when making code changes, and
when upgrading dependencies. Adding browser tests would help reduces the
risk of deploying changes to production that unintentionally change user
functionality.

### Testing frameworks

There are several different testing frameworks available,
including Cypress, Selenium and Playwright. However, for developing Airlock,
the decision was made to use Playwright for its functional testing, and
those tests have been in place since early 2024.

There are advantages in trying to keep the technology stack consistent
across projects: developers have fewer tools to learn, and there can be
sharing of expertise and experience across projects.

### Interaction of pytest-django's `live_server` fixture on OpenCodelists' test fixtures

Playwright uses the `live_server` fixture of pytest-django. The
`live_server` fixture is necessary to run a real Django server for
Playwright to interact with, but using `live_server` has the side effect
of resetting the database state. [^1]

This is a problem for our test setup. OpenCodelists has a `universe` of
fixtures are initialised with the `session` scope, only once per test
session. Many of those `universe` fixtures create database state. When a
subsequent test needing that fixture-supplied database data runs, the
test will fail due to the database reset.

It is possible that the existing `universe` fixtures are redesigned in
future to simplify this problem, making it easier to identify, specify
and recreate individual fixture dependencies for each test. [^2]

With that in mind, we may not want to reimplement fixtures from scratch
specifically for these tests now.

## Decision

We will add automated browser tests that are run with Python using
Playwright and pytest-django's `live_server` fixture to run against a
real Django server. This is how the Airlock tests work.

We will use the existing OpenCodelist `universe` fixtures for now to
setup the coding system data where appropriate, rather than
reimplementing or duplicating those fixtures.

To workaround the problem of losing test database state, we will
reconfigure some of the `universe` fixtures to have a `function` scope
for the functional tests, which initialises once per test for the
functional tests only. This does extra work per test, but allows our
tests to run.

These tests will be run separately from the existing unit tests. This is
partly a design choice — browser tests are generally slower than unit
tests and we do not want to slow down the existing unit test suite — and
partly because of the differing fixture configuration needed as
mentioned above.

## Consequences

* We will have greater assurance that code or dependency changes do not
  result in unintended behaviour changes.
* These tests will need to be maintained, and updated if existing user
  journeys change, or the site design changes to break the existing
  Playwright selectors.
* We will need other tests for important user journeys not covered by
  the initially added tests.
* If we add other important user journeys, new tests will need to be
  added. We could consider addition of appropriate browser tests an
  acceptance criteria for issues involving new user journeys.
* If the fixture setup for testing is changed, we will have to adapt our
  tests accordingly.

[^1]: https://github.com/pytest-dev/pytest-django/blob/0a8473ef4b85dc82a7d33092bcb9b776168ba24f/docs/database.rst#L414-L435
[^2]: https://github.com/opensafely-core/opencodelists/issues/2403
