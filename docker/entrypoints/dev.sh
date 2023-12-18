#!/bin/bash

set -euo pipefail

./manage.py migrate
./manage.py collectstatic --no-input --clear | grep -v '^Deleting '

chown -R 1000:1000 /app/staticfiles

exec "$@"
