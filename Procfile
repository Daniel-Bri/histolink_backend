web: python manage.py migrate && python manage.py create_groups && (python manage.py createsuperuser --noinput || true) && gunicorn kardex.wsgi --bind 0.0.0.0:$PORT
