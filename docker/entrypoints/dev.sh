#!/bin/bash

set -euo pipefail
whoami
./manage.py migrate
./manage.py collectstatic --no-input --clear | grep -v '^Deleting '

exec "$@"
