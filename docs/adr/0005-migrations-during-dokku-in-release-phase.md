# ADR: Run Django Migrations in Dokku Release Phase

Date: 2025-07

## Status

Draft

## Context

Previously, we had a `prod.sh` script that ran the database migrations and then called `exec "$@"` in order to execute whatever command was passed as arguments to the script. The Dockerfile was

```docker
ENTRYPOINT ["/app/docker/entrypoints/prod.sh"]
CMD ["gunicorn", "--config", "/app/deploy/gunicorn/conf.py", "opencodelists.wsgi"]
```

Meaning that when the docker container was run, without additional arguments, this command would execute:

```bash
prod.sh gunicorn --config /app/deploy/gunicorn/conf.py opencodelists.wsgi
```
Causing the migrations to run, and gunicorn to start. You could also pass a command to `docker run` which would then execute (instead of gunicorn) after the migrations.

With this setup, migrations were run every time the container started, including during the web process startup and health checks. This approach had caused issues, including an outage to job-server where migrations were not fully applied.

[Dokku recommend](https://dokku.com/docs/advanced-usage/deployment-tasks/) running database migrations in the `release` phase, which is executed before the new web process is started. This ensures migrations are applied atomically and safely, and that the web process only starts after the database schema is up to date.

## Decision

- **Create** a `release.sh` script that runs the migrations and checks:
  ```bash
  #!/bin/bash
  set -e

  ./manage.py check --deploy
  ./manage.py migrate
  ```
- **Move** the migration and check logic to the `release` phase in the `Procfile` and add the `web` command:
  ```
  release: /usr/bin/env bash /app/deploy/release.sh
  web: gunicorn --config /app/deploy/gunicorn/conf.py opencodelists.wsgi
  ```
- **Remove** the `ENTRYPOINT` from the production Docker image.
- **Delete** the now-obsolete `prod.sh` entrypoint script.
- **Keep** the `CMD` in the Dockerfile so `docker run` will still start Gunicorn by default, but can be overriden

## Consequences

- Migrations are now run in the correct place (Dokku's release phase), before the web process starts.
- Deploys are safer and more predictable, with no risk of web processes starting before migrations are complete.
- No scripts or documentation referenced or used the old `prod.sh` entrypoint, so no further changes were needed following its deletion.
- The dev docker image overwrites the ENTRYPOINT and so is unaffected by its removal
- The `CMD` in the Dockerfile remains, allowing for overriding of the command when running the container.


## Changes

- `docker/Dockerfile`: Removed ENTRYPOINT, kept CMD for Gunicorn.
- `docker/entrypoints/prod.sh`: Deleted.
- `deploy/release.sh`: Created for running migrations and checks.
- `Procfile`: Added release phase for migrations and checks, and web phase for Gunicorn.
