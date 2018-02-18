# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

"""
Database settings for transtats project.
    - this is a temporary as per fedora
    - they should be a part of dev, test only.
"""

import os
from .base import app_config_vars
from .auth import FAS_AUTH

service_name = os.getenv('DATABASE_SERVICE_NAME', '').upper().replace('-', '_')

DATABASE_HOST = os.getenv('DATABASE_SERVICE_NAME', app_config_vars('DATABASE_HOST')) if FAS_AUTH \
    else os.getenv('{}_SERVICE_HOST'.format(service_name)) or app_config_vars('DATABASE_HOST')
DATABASE_PORT = os.getenv('{}_SERVICE_PORT'.format(service_name)) or '' if not FAS_AUTH else ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': app_config_vars('DATABASE_NAME'),
        'USER': app_config_vars('DATABASE_USER'),
        'PASSWORD': app_config_vars('DATABASE_PASSWORD'),
        'HOST': DATABASE_HOST,
        'PORT': DATABASE_PORT,
    }
}
