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
    # allow users to specify python version in .env
    PYTHON_VERSION=${PYTHON_VERSION:-python3.8}

    # create venv and upgrade pip
    test -d $VIRTUAL_ENV || { $PYTHON_VERSION -m venv $VIRTUAL_ENV && $PIP install --upgrade pip; }

    # ensure we have pip-tools so we can run pip-compile
    test -e $BIN/pip-compile || $PIP install pip-tools


_compile src dst *args: virtualenv
    #!/usr/bin/env bash
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
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.prod.txt -nt $VIRTUAL_ENV/.prod || exit 0

    $PIP install -r requirements.prod.txt
    touch $VIRTUAL_ENV/.prod


_env:
    #!/usr/bin/env bash
    test -f .env || cp dotenv-sample .env


# && dependencies are run after the recipe has run. Needs just>=0.9.9. This is
# a killer feature over Makefiles.
#
# ensure dev requirements installed and up to date
devenv: _env prodenv requirements-dev && install-precommit
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.dev.txt -nt $VIRTUAL_ENV/.dev || exit 0

    $PIP install -r requirements.dev.txt
    touch $VIRTUAL_ENV/.dev

    test -f $VIRTUAL_ENV/.playwright || $BIN/playwright install --with-deps chromium && touch $VIRTUAL_ENV/.playwright


# ensure precommit is installed
install-precommit:
    #!/usr/bin/env bash
    BASE_DIR=$(git rev-parse --show-toplevel)
    test -f $BASE_DIR/.git/hooks/pre-commit || $BIN/pre-commit install


# upgrade dev or prod dependencies (specify package to upgrade single package, all by default)
upgrade env package="": virtualenv
    #!/usr/bin/env bash
    opts="--upgrade"
    test -z "{{ package }}" || opts="--upgrade-package {{ package }}"
    FORCE=true {{ just_executable() }} requirements-{{ env }} $opts


# *ARGS is variadic, 0 or more. This allows us to do `just test -k match`, for example.
# Run the python unit tests
test-py *ARGS: devenv
    $BIN/python manage.py collectstatic --no-input && \
    $BIN/python -m pytest \
    -k "not e2e" \
    --cov=builder \
    --cov=codelists \
    --cov=coding_systems \
    --cov=mappings \
    --cov=opencodelists \
    --cov-report html \
    --cov-report term-missing:skip-covered {{ ARGS }}

# Run the js tests
test-js: npm-install
    npm run test


# Run the e2e tests
test-e2e *ARGS: npm-install-no-fnm devenv
    $BIN/python -m pytest e2e_tests -k e2e {{ ARGS }}


# Run the e2e tests
update-screenshots: devenv
    $BIN/python -m pytest e2e_tests  --update-screenshots


# Run all the tests
test: test-js test-py test-e2e

# runs the format (black), sort (isort) and lint (flake8) but does not change any files
check: devenv
    $BIN/black --check .
    $BIN/isort --check-only --diff .
    $BIN/flake8

# fix formatting and import sort ordering
fix: devenv
    $BIN/black .
    $BIN/isort .

# Runs the linter on JS files
check-js: npm-install
    npx prettier static/* --check
    npx eslint static/src/js/builder/* static/src/js/hierarchy.js


# fix js formatting
fix-js: npm-install
    npx prettier static/* --write


# setup/update local dev environment
dev-setup: devenv npm-install
    $BIN/python manage.py migrate
    $BIN/python manage.py collectstatic --no-input --clear | grep -v '^Deleting '


# Run the dev project
run: devenv
    $BIN/python manage.py runserver localhost:8000


# install all JS dependencies
npm-install: check-fnm
    fnm use
    npm ci
    npm run build-dev


# install all JS dependencies without fnm (for CI)
npm-install-no-fnm:
    npm ci
    npm run build-dev


check-fnm:
    #!/usr/bin/env bash
    if ! which fnm >/dev/null; then
        echo >&2 "You must install fnm. See https://github.com/Schniz/fnm."
        exit 1
    fi


# build docker image env=dev|prod
docker-build env="dev": _env
    {{ just_executable() }} docker/build {{ env }}


# run js checks in docker container
docker-check-js:
    {{ just_executable() }} docker/check-js


# run js checks in docker container
docker-check-py: _env
    {{ just_executable() }} docker/check-py


# run python tests in docker container
docker-test-py *args="": _env
    {{ just_executable() }} docker/test-py {{ args }}


# run js tests in docker container
docker-test-js:
    {{ just_executable() }} docker/test-js


# run tests in docker container
docker-test: _env
    {{ just_executable() }} docker/test


# run dev server in docker container
docker-serve: _env
    {{ just_executable() }} docker/serve


# run cmd in dev docker continer
docker-run *args="bash": _env
    {{ just_executable() }} docker/run {{ args }}


# exec command in an existing dev docker container
docker-exec *args="bash": _env
    {{ just_executable() }} docker/exec {{ args }}
