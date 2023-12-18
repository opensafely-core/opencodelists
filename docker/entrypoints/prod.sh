#!/bin/bash

set -euo pipefail

./manage.py migrate
./manage.py collectstatic --no-input

chown -R 10003:10003 /app/staticfiles

exec gunicorn opencodelists.wsgi --config=deploy/gunicorn/conf.py
