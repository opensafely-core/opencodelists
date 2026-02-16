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
dokku$ dokku config:set opencodelists OTEL_EXPORTER_OLTP_ENDPOINT='https://api.honeycomb.io'
dokku$ dokku config:set opencodelists OTEL_EXPORTER_OTLP_HEADERS='x-honeycomb-team=VALIDKEY1234,x-honeycomb-dataset=opencodelists'
dokku$ dokku config:set opencodelists OTEL_SERVICE_NAME='opencodelists'
dokku$ dokku config:set opencodelists DJANGO_SETTINGS_MODULE="opencodelists.settings"
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

Backups are saved to `/var/lib/dokku/data/storage/opencodelists/backup` on dokku3.

### Manually deploying

Merges to the `main` branch will trigger an auto-deploy via GitHub actions.

Note this deploys by building the prod docker image (see `docker/docker-compose.yaml`) and using the dokku [git:from-image](https://dokku.com/docs/deployment/methods/git/#initializing-an-app-repository-from-a-docker-image) command.

To deploy manually:

```
# build prod image locally
just docker-build prod

# tag image and push
export PUBLIC_IMAGE_NAME=ghcr.io/opensafely-core/opencodelists
docker tag opencodelists "$PUBLIC_IMAGE_NAME:latest"
docker push "$PUBLIC_IMAGE_NAME:latest"

# get the SHA for the latest image
SHA=$(docker inspect --format='{{join .RepoDigests "\n"}}' "$PUBLIC_IMAGE_NAME:latest" \
| grep --fixed-strings "$PUBLIC_IMAGE_NAME")
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

### Mapping source files

When updating a mapping you can copy the mapping file(s) to dokku via `scp`.
You should probably test that you can import it in a local development
environment first to ensure that there are no issues with it. By convention, we
place the mapping files to be imported in
/var/lib/dokku/data/storage/mappings/bnfdmd which is mapped within the
container to /storage/mappings/bnfdmd.


### cron jobs

We use a mixture of dokku-managed (see [Backups](#Backups) ) and
[self-managed](https://dokku.com/docs/processes/scheduled-cron-tasks/#self-managed-cron)cron jobs.

For the latter, these are configured via a `cronfile` in `deploy/bin/`
which should be copied to `/etc/cron.d/` using `copy_cronfile.sh` as `sudo`.

All cron jobs (both dokku- and self-managed) call functions from `sentry_cron_functions.sh` to enable
Sentry cron job monitoring. The contents of `deploy/bin` should be copied to
`/var/lib/dokku/data/storage/opencodelists/deploy/bin` (outside container)
or `/storage/deploy/bin` (within container) to support this.

This sentry monitoring requires that the SENTRY_DSN environment variable is set (see above)
