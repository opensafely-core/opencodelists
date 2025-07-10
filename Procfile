release: python manage.py check --deploy && python manage.py migrate
web: gunicorn --config /app/deploy/gunicorn/conf.py opencodelists.wsgi
