release: python manage.py migrate
web: gunicorn cocktail_exchange.wsgi --workers 3 --log-file=-
