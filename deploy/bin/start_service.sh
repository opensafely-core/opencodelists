#!/bin/bash

REPO_ROOT=$(dirname $(dirname $(dirname $0)))
VIRTUALENV_PATH=$REPO_ROOT/venv/bin

source "$VIRTUALENV_PATH/activate"

export PYTHONPATH="$PYTHONPATH:$REPO_ROOT"
export DJANGO_SETTINGS_MODULE="opencodelists.settings"

python "$VIRTUALENV_PATH/gunicorn" opencodelists.wsgi --config "$REPO_ROOT/deploy/gunicorn/conf.py"
