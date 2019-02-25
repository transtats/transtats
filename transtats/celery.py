from __future__ import absolute_import
import os
from celery import Celery


# set the default Django settings module for the 'celery' program.
MODE = os.getenv('TS_APP_MODE', 'dev')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transtats.settings.%s' % MODE)
app = Celery('transtats')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(('dashboard',))


# @app.task(bind=True)
# def debug_task(self):
#     print('Request: {0!r}'.format(self.request))
