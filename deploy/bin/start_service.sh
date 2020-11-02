#!/bin/bash

set -euo pipefail

REPO_ROOT=$(dirname "$(dirname "$(dirname "$0")")")
VIRTUALENV_PATH=$REPO_ROOT/venv/bin

"$REPO_ROOT"/with_environment.sh \
        python \
        "$VIRTUALENV_PATH/gunicorn" \
        opencodelists.wsgi \
        --config "$REPO_ROOT/deploy/gunicorn/conf.py"
