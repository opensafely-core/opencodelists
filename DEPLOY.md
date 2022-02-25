## Deployment

Deployment uses `dokku` and requires the environment variables defined in `dotenv-sample`.
It is deployed to our `dokku2` instance.

## Deployment instructions

### Create app

```sh
dokku$ dokku apps:create opencodelists
dokku$ dokku domains:add opencodelists opencodelists.org opencodelists.opensafely.org
dokku$ dokku git:set opencodelists deploy-branch main
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
dokku$ dokku config:set opencodelists BASE_URLS='https://opencodelists.org,https://opencodelists.opensafely.org'
dokku$ dokku config:set opencodelists DATABASE_URL='sqlite:////storage/db.sqlite3'
dokku$ dokku config:set opencodelists SECRET_KEY='xxx'
dokku$ dokku config:set opencodelists SENTRY_DSN='https://xxx@xxx.ingest.sentry.io/xxx'
dokku$ dokku config:set opencodelists SENTRY_ENVIRONMENT='production'
```

### Backups
Backups are defined as cron jobs in app.json, and managed by dokku

Check cron tasks:
```sh
dokku$ dokku cron:list opencodelists
```

### Manually pushing

Merges to the `main` branch will trigger an auto-deploy via GitHub actions.

Note this deploys by building the prod docker image (see `docker/docker-compose.yaml`) and using the dokku [git:from-image](https://dokku.com/docs/deployment/methods/git/#initializing-an-app-repository-from-a-docker-image) command.


### extras

```sh
dokku$ dokku letsencrypt:enable opencodelists
dokku$ dokku plugin:install sentry-webhook

# turn on/off HTTP auth (also requires restarting the app)
dokku$ dokku http-auth:on opencodelists <user> <password>
dokku$ dokku http-auth:off opencodelists
```
