#!/usr/bin/env bash

set -euo pipefail

./manage.py check --deploy
./manage.py migrate
