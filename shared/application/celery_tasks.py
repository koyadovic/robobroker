from robobroker.celery import app
from django.conf import settings
from shared.domain import periodic_tasks


@app.task(queue=settings.CELERY_QUEUE_NAME)
def every_minute_tick():
    periodic_tasks.execute_minute_tick()


app.conf.beat_schedule = {
    'every-minute-task': {
        'task': 'shared.application.celery_tasks.every_minute_tick',
        'schedule': 60
    }
}
