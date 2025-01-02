# just has no idiom for setting a default value for an environment variable
# so we shell out, as we need VIRTUAL_ENV in the justfile environment
export VIRTUAL_ENV  := `echo ${VIRTUAL_ENV:-.venv}`

# TODO: make it /scripts on windows?
export BIN := VIRTUAL_ENV + "/bin"
export PIP := BIN + "/python -m pip"
# enforce our chosen pip compile flags
export COMPILE := BIN + "/pip-compile --allow-unsafe --generate-hashes"

# Load .env files by default
set dotenv-load := true


# list available commands
default:
    @{{ just_executable() }} --list


# clean up temporary files
clean:
    rm -rf .venv


# ensure valid virtualenv
virtualenv:
    #!/usr/bin/env bash
    set -euo pipefail

    # allow users to specify python version in .env
    PYTHON_VERSION=${PYTHON_VERSION:-python3.12}

    # Error if venv does not contain the version of Python we expect
    if test -d $VIRTUAL_ENV; then
        test -e $BIN/$PYTHON_VERSION || \
        { echo "Did not find $PYTHON_VERSION in $VIRTUAL_ENV (try deleting the virtualenv (just clean) and letting it re-build)"; exit 1; }
    fi

    # create venv and upgrade pip
    test -d $VIRTUAL_ENV || { $PYTHON_VERSION -m venv $VIRTUAL_ENV && $PIP install --upgrade pip; }

    # ensure we have pip-tools so we can run pip-compile
    test -e $BIN/pip-compile || $PIP install pip-tools


_compile src dst *args: virtualenv
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if src file is older than dst file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test "${FORCE:-}" = "true" -o {{ src }} -nt {{ dst }} || exit 0
    $BIN/pip-compile --allow-unsafe --generate-hashes --output-file={{ dst }} {{ src }} {{ args }}


# update requirements.prod.txt if requirements.prod.in has changed
requirements-prod *args:
    {{ just_executable() }} _compile requirements.prod.in requirements.prod.txt {{ args }}


# update requirements.dev.txt if requirements.dev.in has changed
requirements-dev *args: requirements-prod
    {{ just_executable() }} _compile requirements.dev.in requirements.dev.txt {{ args }}


# ensure prod requirements installed and up to date
prodenv: requirements-prod
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.prod.txt -nt $VIRTUAL_ENV/.prod || exit 0

    $PIP install -r requirements.prod.txt
    touch $VIRTUAL_ENV/.prod


_env:
    #!/usr/bin/env bash
    set -euo pipefail

    test -f .env || cp dotenv-sample .env


# && dependencies are run after the recipe has run. Needs just>=0.9.9. This is
# a killer feature over Makefiles.
#
# ensure dev requirements installed and up to date
devenv: _env prodenv requirements-dev && install-precommit
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.dev.txt -nt $VIRTUAL_ENV/.dev || exit 0

    $PIP install -r requirements.dev.txt
    touch $VIRTUAL_ENV/.dev


# ensure precommit is installed
install-precommit:
    #!/usr/bin/env bash
    set -euo pipefail

    BASE_DIR=$(git rev-parse --show-toplevel)
    test -f $BASE_DIR/.git/hooks/pre-commit || $BIN/pre-commit install


# upgrade dev or prod dependencies (specify package to upgrade single package, all by default)
upgrade env package="": virtualenv
    #!/usr/bin/env bash
    set -euo pipefail

    opts="--upgrade"
    test -z "{{ package }}" || opts="--upgrade-package {{ package }}"
    FORCE=true {{ just_executable() }} requirements-{{ env }} $opts


# Upgrade all dev and prod dependencies.
# This is the default input command to update-dependencies action
# https://github.com/opensafely-core/update-dependencies-action
update-dependencies:
    just upgrade prod
    just upgrade dev


# *ARGS is variadic, 0 or more. This allows us to do `just test -k match`, for example.
# Run the python tests
test-py *ARGS: devenv
    $BIN/python manage.py collectstatic --no-input && \
    $BIN/python -m pytest \
    --cov=builder \
    --cov=codelists \
    --cov=coding_systems \
    --cov=mappings \
    --cov=opencodelists \
    --cov-report html \
    --cov-report term-missing:skip-covered {{ ARGS }}

# Run all the tests
test: assets-test test-py

# Run formatting checks
format *args=".": devenv
    $BIN/ruff format --check {{ args }}

# Run linting checks (unused variables etc.)
ruff *args=".": devenv
    $BIN/ruff check {{ args }}

# run the various dev checks but does not change any files
check *args: devenv ruff format

# fix formatting and import sort ordering
fix: devenv
    $BIN/ruff check --fix .
    $BIN/ruff format .

# setup/update local dev environment
dev-setup: devenv assets
    $BIN/python manage.py migrate


# Run the dev project
run: devenv
    $BIN/python manage.py runserver localhost:7000


# Remove built assets and collected static files
assets-clean:
    rm -rf assets/dist
    rm -rf staticfiles


# Install the Node.js dependencies
assets-install *args="":
    #!/usr/bin/env bash
    set -euo pipefail


    # exit if lock file has not changed since we installed them. -nt == "newer than",
    # but we negate with || to avoid error exit code
    test package-lock.json -nt node_modules/.written || exit 0

    npm ci {{ args }}
    touch node_modules/.written


# Build the Node.js assets
assets-build:
    #!/usr/bin/env bash
    set -euo pipefail


    # find files which are newer than dist/.written in the src directory. grep
    # will exit with 1 if there are no files in the result.  We negate this
    # with || to avoid error exit code
    # we wrap the find in an if in case dist/.written is missing so we don't
    # trigger a failure prematurely
    if test -f assets/dist/.written; then
        find assets/src -type f -newer assets/dist/.written | grep -q . || exit 0
    fi

    npm run build
    touch assets/dist/.written


# Ensure django's collectstatic is run if needed
collectstatic: devenv
    ./scripts/collect-me-maybe.sh $BIN/python


# install npm toolchain, build assets, and then collect assets
assets: assets-install assets-build collectstatic


# rebuild all npm/static assets
assets-rebuild: assets-clean assets


assets-run: assets-install
    #!/usr/bin/env bash
    set -euo pipefail

    if [ "$ASSETS_DEV_MODE" == "False" ]; then
        echo "Set ASSETS_DEV_MODE to a truthy value to run this command"
        exit 1
    fi

    npm run dev


assets-lint: assets-install
    npm run lint


assets-test: assets-install
    npm run lint
    npm run test:coverage


# build docker image env=dev|prod
docker-build env="dev": _env
    {{ just_executable() }} docker/build {{ env }}


# run js checks in docker container
docker-check-js: _env
    {{ just_executable() }} docker/check-js


# run js checks in docker container
docker-check-py: _env
    {{ just_executable() }} docker/check-py


# run python tests in docker container
docker-test-py *args="": _env
    {{ just_executable() }} docker/test-py {{ args }}


# run js tests in docker container
docker-test-js: _env
    {{ just_executable() }} docker/test-js


# run tests in docker container
docker-test: _env
    {{ just_executable() }} docker/test


# run dev server in docker container
docker-serve env="dev" *args="": _env
    {{ just_executable() }} docker/serve {{ env }} {{ args }}


# run cmd in dev docker continer
docker-run *args="bash": _env
    {{ just_executable() }} docker/run {{ args }}


# exec command in an existing dev docker container
docker-exec *args="bash": _env
    {{ just_executable() }} docker/exec {{ args }}


# run tests in docker container
docker-smoke-test host="http://localhost:7000": _env
    {{ just_executable() }} docker/smoke-test {{ host }}
