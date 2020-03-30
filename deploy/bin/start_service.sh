#!/bin/bash

REPO_ROOT=$(dirname $(dirname $(dirname $0)))
VIRTUALENV_PATH=$REPO_ROOT/venv/bin

source "$VIRTUALENV_PATH/activate"

export PYTHONPATH="$PYTHONPATH:$REPO_ROOT"
export DJANGO_SETTINGS_MODULE="opencodelists.settings"

python "$REPO_ROOT/manage.py" runserver 0.0.0.0:8001
