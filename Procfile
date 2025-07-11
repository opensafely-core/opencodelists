# Release phase - runs migrations before the app starts
release: sh -c "./manage.py check --deploy && ./manage.py migrate"
web: gunicorn --config /app/deploy/gunicorn/conf.py opencodelists.wsgi
