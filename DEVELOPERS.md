# OpenCodelists for developers

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

## Production database and backups

Production data is stored on dokku3 at `/storage/` within the container layer
file system. This maps to `/var/lib/dokku/data/storage/opencodelists` in the
host operating system's file system. See also [deployment notes](DEPLOY.md)).

`/storage/db.sqlite3` is the core Django database.

`/storage/coding_systems` contains the coding system databases. These are
read-only. Refer to their README files for information on the source data and
creation process.

The core database is fully backed up daily on the local file system. Coding
system databases are not backed up locally but can be recreated from source.
Weekly backups of the droplets allow a restore of the file system.

The core database backups are located at `/storage/backup/db`. They are created
by `deploy/bin/backup.sh` scheduled via `cron` as configured in `app.json`.
Backups are taken via the `sqlite3` `.backup` command . These are effectively
copies of the database file. They are compressed to save space.

To restore from a backup, use the command-line tool to create a fresh temporary
backup of the current state of the database (in case anything gones wrong),
then restore from the decompressed backup file. On the production server:

```sh
dokku enter opencodelists
sqlite3 /storage/db.sqlite3 ".backup /storage/backup/previous-db.sqlite3"

zstd -d /storage/backup/db/{PATH_TO_BACKUP_ZST} -o /storage/backup/restore-db.sqlite3
sqlite3 /storage/db.sqlite3 ".restore /storage/backup/restore-db.sqlite3"
```

When all is confirmed working with the restore, you can delete
`previous-db.sqlite3` and `restore-db.sqlite3`.

The latest backup is available via symlink at
`/storage/backup/db/latest-db.sqlite3.zst`.
This backup is a verbatim copy of the live data,
and so contains user personal data and API keys.

For development purposes,you should use the sanitised copy at
`/storage/backup/db/sanitised-latest-db.sqlite3.zst`.  You can use `scp`, `zstd
-d` and `sqlite3 ".restore"` to bring your local database into the same state as
the production database.  You may also wish to retrieve some or all of the
coding systems databases, otherwise you will not be able to view codelists that
require them or build codelists.  Refer to the team manual [OpenCodelists
playbook](https://bennett.wiki/tech-group/playbooks/opencodelists/) for how to
do those tasks on our infrastructure.

## Local development

### Prerequisites:

- **Python v3.12.x**
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

### Build a lightweight local development setup
Run the `just build-dbs-for-local-development` recipe to create a new local core database and a few coding system release databases, then populate them with test fixture data.

Before running, refer to the [justfile](/justfile) and the [setup_local_dev_databases.py](opencodelists/management/commands/setup_local_dev_databases.py) management command for implementation details.

After setup is complete, you can:
 - Log in as `localdev`
 - Search for 'arthritis', 'tennis', and 'elbow'
 - Build codelists with the concepts returned from these searches
 - View a BNF codelist, a minimal codelist, and a new-style SNOMED CT codelist

Note: This setup does not support local development using mappings.

### Run local development server

The development server can be run locally, as described below, or in [docker](#using-docker-for-development-and-tests).

To use Django Debug Toolbar in development, set `DJANGO_DEBUG_TOOLBAR`.
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

Run a command in the dev docker container
```sh
just docker-run <command>
```

Build and run a prod container locally (for testing/QA)
```sh
just docker-build prod
docker run -it --entrypoint /bin/bash  opencodelists
```

### Using Playwright to update screenshots in docs

There is a functional test, [test_docs_screenshots.py](opencodelists/tests/functional/test_docs_screenshots.py), which generates screenshots for use in the documentation.

**If your changes result in altered or added screenshots, generate these with Playwright.**

By default screenshots are not generated unless you set the `TAKE_SCREENSHOTS` environment variable to `True` - either in your `.env` file or by executing the test as follows:

```sh
IN_PRODUCTION=True TAKE_SCREENSHOTS=True just test-functional opencodelists/tests/functional/test_docs_screenshots.py
```

`IN_PRODUCTION=True` is required to disable the development banner that may be in screenshots otherwise.

Only images that have changed will be committed to github - but it's worth noting that:
- running the tests in different environments will likely lead to subtle visual differences and so may appear different even when nothing has changed
- any screenshots that contain date or time stamps, or have hash ids, may change everytime the command is run


## Other production maintenance tasks

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

### Deleting published codelists

:warning: *We should not delete published codelists,
except in very rare circumstances.*
It is difficult to guarantee that codelists are not being anywhere at all
— there may be uses other than for OpenSAFELY projects.

However, on rare occasions,
users may request deletion of *published* codelists or their versions.

Note that users can delete unpublished versions of codelists,
or entirely unpublished codelists themselves.
Users cannot delete published versions of codelists.

These requests should be limited to user-owned codelists,
not organisation codelists.

#### Process for deleting a single version of a codelist

First, visit the codelist URL of interest
and note down the version ID hash on the page.

On dokku3:

1. Start `shell_plus` which loads the database models for you:
   ```sh
   $ dokku run opencodelists python manage.py shell_plus
   ```
2. Access the specific version of the codelist:
   ```pycon
   >>> version = CodelistVersion.objects.get_by_hash("<hash>")
   ```
3. Delete the **codelist version**:
   ```pycon
   >>> version.delete()
   ```

#### Process for deleting a codelist entirely

First, visit the codelist URL of interest
and note down the version hash on the page.

On dokku3:

1. Start `shell_plus` which loads the database models for you:
   ```sh
   $ dokku run opencodelists python manage.py shell_plus
   ```
2. Access the codelist through the specified version:
   ```pycon
   >>> version = CodelistVersion.objects.get_by_hash("<hash>")
   >>> codelist = version.codelist
   ```
3. Delete the **codelist and all of its versions**:
   ```pycon
   >>> codelist.delete()
   ```

### Import codelists from an xlsx file

See [codelists/scripts/README.md](codelists/scripts/README.md#bulk-import-codelists-from-an-xlsx-file)

### Experimental coding systems

When adding a new coding system it is possible to get user feedback by deploying it as an experimental coding system. Once the required methods of the parent class `BuilderCompatibleCodingSystem` have been implemented, you can set the `is_experimental` flag to `True`. This then makes the coding system available for new codelists, but only if the user navigates to this URL rather than clicking the "create new codelist" button:

/users/<username>/new-codelist/?include_experimental_coding_systems

The experimental coding systems have visible warnings to ensure they are not used accidentally.

## Updating mappings

See the relevant README in each of the subdirectories inside [mappings/](mappings/).


## Migrations deployment strategy

When deploying PRs that include migrations, there's a brief period where the
old container may execute against a database that has been migrated, before
cutting over to the new container. Additionally, migrations may execute during
a deployment that ultimately fails, leaving the old container running. Either
scenario can result in unhandled exceptions if the old container is
incompatible with the migrated database.

Django allows for model-database inconsistencies, raising database-layer errors
only when actual issues arise. Certain changes, like adding a table or column,
are generally safe because the old code won’t query the new fields. Similarly,
making a field nullable is safe -- it won't cause database access failures and
impacts application code only if non-null values are required.

Problems arise when a table or column is removed and old code tries to access
it, or when a field is made non-nullable and old code attempts to insert null
values. For these cases, a safer deployment strategy is to split changes into
multiple PRs. First, deploy the application changes in one PR. Then, deploy the
migration in a separate PR. This approach ensures that during the migration PR
deployment, the old container is compatible with both the pre- and
post-migration database states, mitigating risks if the deployment or migration
fails.

Renaming a table or column is more complex. A good approach is to use three
PRs: first, a PR with models and migrations to create the new table or column
and replicate existing data; then a PR updating the application code to use the
new table/column; and finally, a PR to remove the old field or model and the
corresponding migration.

## Testing deployments locally

Please refer to the [local deployment document](./deploy/local/LOCAL_DEPLOYMENT_TESTING.md) for instructions on how to test deployments locally.
