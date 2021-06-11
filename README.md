# OpenCodelists

OpenCodelists is an open platform for creating and sharing codelists of clinical terms and drugs.

It is part of the [OpenSAFELY](https://opensafely.org) project, and is served from [www.opencodelists.org](https://www.opencodelists.org).


## Repo structure

There are the usual config files in the root of the repo.

#### `opencodelists/`

The "project root", containing `settings.py` etc.  Also an app, with models for users, organisations, and projects.

#### `codelists/`

The app with models and views for viewing, downloading, creating, and updating codelists.

#### `coding_systems/`

A directory containing one app per coding system.  Each of these apps will have a common structure, which has not yet been codified.

#### `mappings/`

A directory containing one app per mapping between coding systems.  Each of these apps will have a common structure, which has not yet been codified.

#### `templates/`

Templates.

#### `deploy/`

Resources for deployment.  Deployment is via Fabric.

#### `scripts/`

A place to put scripts to be run via [runscript](https://django-extensions.readthedocs.io/en/latest/runscript.html).


## Development

To install dependencies:

* Run `pip install -r requirements.txt`
* Run `npm install`

To update dependencies:

* Edit `requirements.in` and run `pip-compile`
* Run `npm --save[-dev] ...`

To build JS:

* Run `npm run watch`

To run tests:

* `pytest` (or `./manage.py test`)
* `npm run test`

To check formatting:

* `make format lint sort`

To fix formatting:

* `make fix`

To set up tooling via a pre-commit hook:

* `pre-commit install`

To use Django Debug Toolbar in development, set `DDT_ENABLED`.
It is not enabled by default because it adds tens of seconds to the load time of some pages.

## Deployment

See the [deployment notes](DEPLOY.md).

# About the OpenSAFELY framework

The OpenSAFELY framework is a Trusted Research Environment (TRE) for electronic
health records research in the NHS, with a focus on public accountability and
research quality.

Read more at [OpenSAFELY.org](https://opensafely.org).
