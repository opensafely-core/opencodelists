# OpenCodelists for developers

## Repo structure

There are the usual config files in the root of the repo.

#### `opencodelists/`

The "project root", containing `settings.py` etc. Also an app, with models for users, organisations, and projects.

#### `codelists/`

The app with models and views for viewing, downloading, creating, and updating codelists.

#### `coding_systems/`

A directory containing one app per coding system. Each of these apps will have a common structure, which has not yet been codified.

#### `mappings/`

A directory containing one app per mapping between coding systems. Each of these apps will have a common structure, which has not yet been codified.

#### `templates/`

Templates.

#### `deploy/`

Resources for deployment. Deployment is via dokku (see [deployment notes](DEPLOY.md)).

#### `scripts/`

A place to put scripts to be run via [runscript](https://django-extensions.readthedocs.io/en/latest/runscript.html).


# Notes for developers

## Production database and backups

The production database and backups are located at  `/var/lib/dokku/data/storage/opencodelists` on dokku1 (see also [deployment notes](DEPLOY.md)).


## Local development

### Prerequisites:

- **Python v3.8.x**
- **Pip**
- **[fnm](#install-fnm)**
- **[Just](#install-just)**

### Install just

```sh
# macOS
brew install just

# Linux
# Install from https://github.com/casey/just/releases

# Add completion for your shell. E.g. for bash:
source <(just --completions bash)

# Show all available commands
just #  shortcut for just --list
```

### Install fnm

See https://github.com/Schniz/fnm#installation.

### Run local development server

The development server can be run locally, as described below, or in [docker](#using-docker-for-development-and-tests).

To use Django Debug Toolbar in development, set `DDT_ENABLED`.
It is not enabled by default because it adds tens of seconds to the load time of some pages.

#### Set up/update local dev environment

```sh
just dev-setup
```

#### Run local django server

```sh
just run
```

Access at http://localhost:8000


#### Run tests

```sh
# python tests and coverage
just test-py

# run specific test with usual pytest syntax
just test-py <path/to/test>::<test name>

# js tests
just test-js

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
just check-js
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

Run a command in the dev docker containter
```sh
just docker-run <command>
```
