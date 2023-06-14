## Deployment

Deployment uses `dokku` and requires the environment variables defined in `dotenv-sample`.
It is deployed to our `dokku3` instance.

## Deployment instructions

### Create app

On dokku3, as the `dokku` user:

```sh
dokku$ dokku apps:create opencodelists
dokku$ dokku domains:add opencodelists www.opencodelists.org
```

### Create storage for sqlite db and backups and load db into it
```sh
dokku$ mkdir /var/lib/dokku/data/storage/opencodelists
dokku$ chown dokku:dokku /var/lib/dokku/data/storage/opencodelists
# If we have an existing db to load in
dokku$ cp ./opencodelists-db.sqlite3 /var/lib/dokku/data/storage/opencodelists/db.sqlite3
dokku$ chown dokku:dokku /var/lib/dokku/data/storage/opencodelists/*
dokku$ dokku storage:mount opencodelists /var/lib/dokku/data/storage/opencodelists/:/storage
```

### Configure app

```sh
# set environment variables
dokku$ dokku config:set opencodelists IN_PRODUCTION=True
dokku$ dokku config:set opencodelists BASE_URLS='https://www.opencodelists.org'
dokku$ dokku config:set opencodelists DATABASE_URL='sqlite:////storage/db.sqlite3'
dokku$ dokku config:set opencodelists DATABASE_DIR='/storage'
dokku$ dokku config:set opencodelists SECRET_KEY='xxx'
dokku$ dokku config:set opencodelists SENTRY_DSN='https://xxx@xxx.ingest.sentry.io/xxx'
dokku$ dokku config:set opencodelists EMAIL_BACKEND='anymail.backends.mailgun.EmailBackend'
dokku$ dokku config:set opencodelists MAILGUN_API_KEY='xxx'
```

### Configure nginx
Dokku does most of the nginx configuration for us, however specific config can be updated
with the `nginx:set` command.

To allow uploads of CSV files that are larger than the default allowed by nginx, run:

```sh
dokku$ dokku nginx:set opencodelists client-max-body-size 20m
```

Restart the app to regenerate the nginx config:
```sh
dokku$ dokku ps:restart opencodelists
```

View nginx config:
```sh
dokku$ dokku nginx:show-config opencodelists
```

### Backups
Backups are defined as cron jobs in app.json, and managed by dokku

Check cron tasks:
```sh
dokku$ dokku cron:list opencodelists
```

Backups are saved to `/var/lib/dokku/data/storage/opencodelists` on dokku3.

### Manually deploying

Merges to the `main` branch will trigger an auto-deploy via GitHub actions.

Note this deploys by building the prod docker image (see `docker/docker-compose.yaml`) and using the dokku [git:from-image](https://dokku.com/docs/deployment/methods/git/#initializing-an-app-repository-from-a-docker-image) command.

To deploy manually:

```
# build prod image locally
just docker-build prod

# tag image and push
docker tag opencodelists ghcr.io/opensafely-core/opencodelists:latest
docker push ghcr.io/opensafely-core/opencodelists:latest

# get the SHA for the latest image
SHA=$(docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/opensafely-core/opencodelists:latest)
```

On dokku3, as the `dokku` user:
```
dokku$ dokku git:from-image opencodelists <SHA>
```

### extras

Requires the `sentry-webhook` and `letsencrypt` plugins.


```sh
# Check plugins installed:
dokku$ dokku plugin:list

# enable letsencrypt (must be run as root)
root$ dokku config:set --no-restart opencodelists DOKKU_LETSENCRYPT_EMAIL=<e-mail>
root$ dokku letsencrypt:enable opencodelists

# turn on/off HTTP auth (also requires restarting the app)
dokku$ dokku http-auth:on opencodelists <user> <password>
dokku$ dokku http-auth:off opencodelists
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
