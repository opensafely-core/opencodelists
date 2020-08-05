# OpenCodelists

OpenCodelists is a rapidly-changing work in progress.  It will be a platform for the development and dissemination of codelists for use in medical research.

It is part of the [OpenSAFELY](https://opensafely.org) project, and is currently served from [codelists.opensafely.org](https://codelists.opensafely.org).

It hosts codelists used in our paper on [factors associated with COVID-19-related hospital death in the linked electronic health records of 17 million adult NHS patients](https://opensafely.org/outputs/2020/05/covid-risk-factors/).


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

To update dependencies:

* Edit `requirements.in`
* Run `pip-compile`

To run tests:

* `pytest` (or `./manage.py test`)

To check formatting:

* `make format lint sort`

To fix formatting:

* `make fix`

To set up tooling via a pre-commit hook:

* `pre-commit install`

## Deployment

OpenCodelists is currently deployed to smallweb1.  Deployment is with fabric:

```
fab deploy
```

You will need to configure SSH agent forwarding in your `~/.ssh/config`, e.g.

    Host smallweb1.ebmdatalab.net
    ForwardAgent yes
    User <your user on smallweb1>


macOS users will need to configure their SSH Agent to add their key by default as per [GitHub's Docs](https://docs.github.com/en/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#adding-your-ssh-key-to-the-ssh-agent).

On the server, use `with_environment.sh` to run a management command in the virtual environment with the correct settings:

```
./with_environment.sh ./manage.py shell
```
