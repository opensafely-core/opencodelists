#!/usr/bin/env bash
set -euo pipefail

# allow just file to pass current venv python through
python=${1:-python}

if ! $python -c 'import django'; then
    echo "Cannot import django - are you in the right virtualenv?"
    exit 1
fi


staticfiles="$($python manage.py print_settings STATIC_ROOT --format value)"
sentinel="$staticfiles/.written"
gitkeep="$staticfiles/.keep"
run=false

if ! test -f "$sentinel"; then
    run=true
else
    staticdirs="$($python manage.py print_settings STATICFILES_DIRS --format value | sed -e "s/[]',[]//g")"

    if [[ "$staticdirs" == *"PosixPath"* ]]; then
        echo "ERROR: invalid STATICFILES_DIRS values - they should be strings not paths"
        exit 1
    fi
    # shellcheck disable=SC2086
    find $staticdirs -type f -newer "$sentinel" | grep -q . && run=true
fi

if test "$run" != "true"; then
    echo "Skipping collectstatic, no changes detected"
    exit 0
fi

echo "Running collectstatic, src file changes detected"
$python manage.py collectstatic --no-input --clear | grep -v '^Deleting '
touch "$gitkeep"
touch "$sentinel"
