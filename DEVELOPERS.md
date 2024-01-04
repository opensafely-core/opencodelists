# OpenCodelists for developers

## Repo structure

There are the usual config files in the root of the repo.

#### `opencodelists/`

The "project root", containing `settings.py` etc. Also an app, with models for users, organisations, and projects.

#### `codelists/`

The app with models and views for viewing, downloading, creating, and updating codelists.

#### `coding_systems/`

A directory containing one app per coding system. Each of these apps contains a `coding_system.py` which defines a common interface, and an `import_data.py` which contains
code for importing new data.

Each directory contains a README with information about the underlying data.

##### `coding_systems/versioning`
An app that holds information about coding system releases.

Each release of a coding system is imported into a separate sqlite database, and has a `CodingSystemRelease` instance associated with it which allows us to identify the specific
release database to use to retrieve codes and terms for a codelist version..

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

The production database and backups are located at  `/var/lib/dokku/data/storage/opencodelists` on dokku3 (see also [deployment notes](DEPLOY.md)).


## Local development

### Prerequisites:

- **Python v3.11.x**
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

Access at http://localhost:7000


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

### Manually creating and updating codelist versions

Currently OpenCodelists handles multiple coding system releases, however it can't always handle
new versions of codelists when the coding system has changed significantly since the original
version was created. When a user creates a new version of a codelist, the searches from the
original codelist are re-run. If these searches bring back any new codes, the version will fail
to be created.  Users will see a message prompting them to contact tech-support:

```
Codes with unknown status found when creating new version; this is likely due to an update in
the coding system. Please contact tech-support for assistance.
```

The codelist version can be manually created by running the following command on dokku3:

```
dokku$ dokku run opencodelists \
    python manage.py create_and_update_draft <original version hash> --author <username>
```

The command will create a new draft version, and will assign statuses to each unknown code where
possible. i.e. if a new code has an ancestor code that is included, it will be implicitly
included (`(+)` status), and if it has an ancestor code that is excluded, it will be implictly
excluded (`(-)` status).  The command will output a list of codes that were returned as "unknown"
(`?`) status from the re-run searches, and have been assigned an assumed status. These should be passed on to the user to confirm.

### Import codelists from an xlsx file

See [codelists/scripts/README.md](codelists/scripts/README.md#bulk-import-codelists-from an-xlsx-file)
