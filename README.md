# robobroker
robobroker

# Running Celery + server local
```
# local server
python manage.py runserver 7000

# celery beat
celery beat -A robobroker.celery

# celery worker
celery worker -A robobroker.celery
```
