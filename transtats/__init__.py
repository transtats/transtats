#!/usr/bin/env python
from __future__ import absolute_import
import os
import sys

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app


__appname__ = "Transtats"
__version__ = '0.8'
__release__ = '0.8.4'
__description__ = "Help track language translations across releases and automate process workflows."
__title__ = "Automate Translation Workflows"


__all__ = ['__appname__', '__version__', '__release__', '__description__', '__title__', 'celery_app']

MODE = os.getenv('TS_APP_MODE', 'dev')


def prepare_env():
    # Update the default settings environment variable based on current mode.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transtats.settings.%s' % MODE)


def manage():
    # Prepare the TS environment.
    prepare_env()
    # Execute
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
