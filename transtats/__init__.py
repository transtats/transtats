#!/usr/bin/env python
import os
import sys

__appname__ = "Transtats"
__version__ = '0.1.6-rc.2'

__all__ = ['__appname__', '__version__']

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
