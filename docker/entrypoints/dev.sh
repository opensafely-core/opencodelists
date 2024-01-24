#!/bin/bash

set -euo pipefail
./manage.py migrate
./manage.py collectstatic --no-input --clear | grep -v '^Deleting '
cp -r /opt/assets/. /opt/assetsout/

exec "$@"
