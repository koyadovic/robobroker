from ad_signum.celery import app
from django.conf import settings
from shared.domain import periodic_tasks
from issues.domain import services as issues_services


@app.task(queue=settings.CELERY_QUEUE_NAME)
def every_minute_tick():
    try:
        periodic_tasks.execute_minute_tick()
    except Exception as e:
        issues_services.register_exception(e)


app.conf.beat_schedule = {
    'every-minute-task': {
        'task': 'shared.application.celery_tasks.every_minute_tick',
        'schedule': 60
    }
}
