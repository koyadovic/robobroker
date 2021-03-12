import os

from .base import *


DEBUG = False
ALLOWED_HOSTS = ['*']


MEDIA_ROOT = os.path.join('/var/www/robobroker/media_test/' if TESTING else '/var/www/robobroker/media/')
STATIC_ROOT = '/var/www/robobroker/static/'


import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ['SENTRY_DSN'],
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)
