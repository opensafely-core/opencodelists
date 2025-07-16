#!/usr/bin/env bash

# Gets executed during dokku's release phase as specified in Procfile.
# Currently just runs manage.py commands to check and migrate the database.
# This is where dokku recommends running db migrations.

set -euo pipefail

./manage.py check --deploy
./manage.py migrate
