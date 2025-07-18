#!/usr/bin/env bash

# Gets executed during dokku's release phase as specified in Procfile.
# This is where dokku recommends running db migrations.

set -euo pipefail

./manage.py check --deploy
./manage.py migrate
