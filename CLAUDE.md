# Generate coding guidelines

When writing python code, you MUST follow these principles:

- When adding to a file, or writing tests, always follow the patterns and conventions in the existing codebase
- NEVER propose code that catches bare exceptions
- ALWAYS allow exceptions to propagate to the user, unless instructed otherwise. I want things to fail noisily!!
- Always start by thinking about tests; update an existing one, or write a new one
- Keep module sizes small
- Code should be easy to read and understand.
- Keep the code as simple as possible. Avoid unnecessary complexity.
- Use meaningful names for variables, functions, etc. Names should reveal intent.
- Prefer long names for functions over the use of dotted namespaces.
- Functions should be small and do one thing well. They should not exceed a few lines.
- Function names should describe the action being performed.
- Prefer fewer arguments in functions. Ideally, aim for no more than two or three.
- Only use comments when necessary, as they can become outdated. Instead, strive to make the code self-explanatory.
- When comments are used, they should add useful information that is not readily apparent from the code itself.
- Properly handle errors and exceptions to ensure the software's robustness.
- Use exceptions rather than error codes for handling errors.
- Consider security implications of the code. Implement security best practices to protect against vulnerabilities and attacks.
- Adhere to these 4 principles of Functional Programming:
  - Pure Functions
  - Immutability
  - Function Composition
  - Declarative Code
- Avoid object oriented programming.


# Testing and adding modules

* Check CLAUDE.md for coding guidelines and how to run tests
* To add a python dependency, add it to requirements.prod.in and then run `just requirements-prod`
* To run all python tests, run `just test-py`
* To run specific test with usual pytest syntax: `just test-py <path/to/test>::<test name>`
* To start a server at http://127.0.0.1:9090/, which you could test using your playwright tools (browser_navigate, browser_click, etc): `just run`

# OpenCodelists for developers

This is a django app. Follow existing conventions in code wherever possible.

## Repo structure

There are several config files in the root directory of the repo.

#### `opencodelists/`

The project configuration module, containing the main `settings.py`, `urls.py`
and `wsgi.py`. Also an app, with models for users and organisations.

#### `codelists/`

App with models and views for viewing, downloading, creating, and updating codelists.

#### `builder/`

App with forms, views, and actions for the codelist builder in the web UI.

#### `coding_systems/`

A directory containing one app per coding system. Each of these apps contains a
`coding_system.py` which defines a common interface, and an `import_data.py`
which contains code for importing new data.

Each directory contains a README with information about the underlying data.

##### `coding_systems/versioning`
An app that holds information about coding system releases.

Each release of a coding system is imported into a separate sqlite database,
and has a `CodingSystemRelease` instance associated with it which allows us to
identify the specific release database to use to retrieve codes and terms for a
codelist version.

#### `mappings/`

A directory containing one app per mapping between coding systems. Each of
these apps will have an `import_data.py`, a `mappers.py` and a `models.py`
containing a `Mapping` class.

#### `conversions/`

App with views/forms for applying a mapping to convert a codelist from one
coding system to another.

#### `services/`

Code for services used by multiple apps such as logging or OTel tracing.

#### `superusers/`

App with staff/admin-facing functionality. A view to list all the codelists
(the main `codelists` app index only shows codelists that come from
organisations).

#### `templates/`

Django templates.

#### `static/`

Static files such as images.

#### `assets/`

Frontend assets such as JavaScript and CSS.

#### `deploy/`

Resources for deployment. Deployment is via dokku (see [deployment notes](DEPLOY.md)).

#### `docker/`

Docker files for building and testing development and production images of the site.

#### `scripts/`

A place to put scripts to be run via [runscript](https://django-extensions.readthedocs.io/en/latest/runscript.html).

#### `docs/`

Developer-facing documentation including architecture decision records (ADRs).

#### `userdocs/`

Simple app serving user-facing documentation at docs/. Each document is a
markdown file for ease of editing and they are served by a generic view.

# Notes for developers

## actions.py business logic layer

We encapsulate business logic in a module called `actions.py` in each app that
affects state: the `builder`, `codelists`, and `opencodelists` apps.

Please refer to [this ADR](docs/adr/0004-business-logic-layer.md) for more information.



#### Set up/update local dev environment

```sh
just dev-setup
```

#### Run local django server

```sh
just run
```

Access at http://localhost:7000


#### Run tests

```sh
# python tests and coverage
just test-py

# run specific test with usual pytest syntax
just test-py <path/to/test>::<test name>

# run Playwright functional tests
just test-functional

# watch a specific functional test in browser, slowed down
# This is useful in combination with script pausing when writing tests:
# https://playwright.dev/python/docs/api/class-page#page-pause
just test-functional <path/to/test>::<test name> --headed --slowmo=500

# debug a specific functional test
# See https://playwright.dev/python/docs/debug for more information.
PWDEBUG=1 just test-functional <path/to/test>::<test name>

# js tests
just assets-test

# all tests
just test
```

#### Check/Fix formatting, linting, sorting
```sh
# check python files (black, isort, flake8)
just check

# fix black and isort
just fix

# js linting
just assets-lint
```

### Using docker for development and tests

Run a local development server in docker:

```sh
just docker-serve
```

Run the python tests in docker
```sh
just docker-test-py
```

To run named test(s) or pass additional args, pass paths and args as you normally would to pytest:
```sh
just docker-test-py tests/reports/test_models.py::test_report_model_validation -k some-mark --pdb
```

Run the JS tests in docker
```sh
just docker-test-js
```
