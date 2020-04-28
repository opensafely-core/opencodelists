#!/bin/bash

REPO_ROOT=$(dirname $0)
VIRTUALENV_PATH=$REPO_ROOT/venv/bin

source "$VIRTUALENV_PATH/activate"
source "$REPO_ROOT/environment"

export PYTHONPATH="$PYTHONPATH:$REPO_ROOT"
export DJANGO_SETTINGS_MODULE="opencodelists.settings"

exec "$@"
