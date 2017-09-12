#!/usr/bin/env python
import os
import sys

# update dashboard/templates/base.html also
__version__ = '0.1.3'

__all__ = ['__version__']

MODE = 'dev'


def prepare_env():
    # Update the default settings environment variable based on current mode.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transtats.settings.%s' % MODE)


def manage():
    # Prepare the TS environment.
    prepare_env()
    # Execute
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
