from billiard.exceptions import WorkerLostError

from .base import *


def before_send(event, hint):
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, (WorkerLostError,)):
            return None
    return event


if not TESTING:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn="https://2fe387acbc414f0d9954e78b3da1535c@o230030.ingest.sentry.io/5621802",
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
        before_send=before_send,
    )
