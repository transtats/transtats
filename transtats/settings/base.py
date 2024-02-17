"""
Django base settings for transtats project.

Generated by 'django-admin startproject' using Django 1.9.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

# Stdlib imports
import os
import json

from celery.schedules import crontab

# Core Django imports
from django.core.exceptions import ImproperlyConfigured

__all__ = [
    'BASE_DIR',
    'SECRET_KEY',
    'TS_AUTH_SYSTEM',
    'INSTALLED_APPS',
    'MIDDLEWARE',
    'ROOT_URLCONF',
    'TEMPLATES',
    'AUTHENTICATION_BACKENDS',
    'SESSION_ENGINE',
    'SESSION_COOKIE_SECURE',
    'WSGI_APPLICATION',
    'LOGIN_REDIRECT_URL',
    'CELERY_BROKER_URL',
    'CELERY_TASK_SERIALIZER',
    'CELERY_RESULT_SERIALIZER',
    'CELERY_ACCEPT_CONTENT',
    'CELERY_ENABLE_UTC',
    'CELERY_BEAT_SCHEDULE',
    'DATABASES',
    'MIGRATE_INITIAL_DATA',
    'AUTH_PASSWORD_VALIDATORS',
    'LANGUAGE_CODE',
    'TIME_ZONE',
    'USE_I18N',
    'USE_L10N',
    'USE_TZ',
    'STATICFILES_DIRS',
    'STATIC_URL',
    'STATIC_ROOT',
    'CRISPY_TEMPLATE_PACK',
    'CACHES',
    'REST_FRAMEWORK'
]

# Imports from your apps

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/


def get_secret(config_var):
    """Get the secret variable or return explicit exception."""
    file_location = os.path.dirname(os.path.abspath(__file__)) + "/"
    try:
        with open(file_location + "keys.json") as f:
            return json.loads(f.read())[config_var]
    except FileNotFoundError:
        with open(file_location + "keys.json.example") as f:
            return json.loads(f.read()).get(config_var, '')
    except KeyError:
        error_msg = "Set the {0} environment variable.".format(config_var)
        raise ImproperlyConfigured(error_msg)


def app_config_vars(var):
    return os.environ[var] if os.environ.get(var) else get_secret(var)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = app_config_vars('DJANGO_SECRET_KEY')
TS_AUTH_SYSTEM = app_config_vars('TS_AUTH_SYSTEM')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'crispy_forms',
    'corsheaders',
    'rest_framework',
    'django_celery_beat',
    'dashboard.apps.DashboardConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'transtats.middleware.CustomMiddleware',
]

ROOT_URLCONF = 'transtats.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.app_info'
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = False

WSGI_APPLICATION = 'transtats.wsgi.application'

LOGIN_REDIRECT_URL = '/'
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_ENABLE_UTC = True

CELERY_BEAT_SCHEDULE = {
    'task_sync_packages_with_platform': {
        'task': 'dashboard.tasks.task_sync_packages_with_platform',
        'schedule': crontab(minute='0', hour='19'),
    },
    'task_sync_packages_with_build_system': {
        'task': 'dashboard.tasks.task_sync_packages_with_build_system',
        'schedule': crontab(minute='30', hour='0'),
    },
}

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

service_name = os.getenv('DATABASE_SERVICE_NAME', '').upper().replace('-', '_')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': app_config_vars('DATABASE_NAME'),
        'USER': app_config_vars('DATABASE_USER'),
        'PASSWORD': app_config_vars('DATABASE_PASSWORD'),
        'HOST': os.getenv('{}_SERVICE_HOST'.format(service_name)) or app_config_vars('DATABASE_HOST'),
        'PORT': os.getenv('{}_SERVICE_PORT'.format(service_name)) or '',
    }
}

MIGRATE_INITIAL_DATA = True

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATICFILES_DIRS = (

    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # TODO: find some method to serve only specific files downloaded from npm possible solutions gulp, grunt
    os.path.join(BASE_DIR, "node/node_modules/"),
    os.path.join(BASE_DIR, "static"),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'staticfiles')

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'filters': {
#         'require_debug_false': {
#             '()': 'django.utils.log.RequireDebugFalse'
#         }
#     },
#     'handlers': {
#         'mail_admins': {
#             'level': 'ERROR',
#             'filters': ['require_debug_false'],
#             'class': 'django.utils.log.AdminEmailHandler'
#         }
#     },
#     'loggers': {
#         'django.request': {
#             'handlers': ['mail_admins'],
#             'level': 'ERROR',
#             'propagate': True,
#         },
#     }
# }

# django-crispy-forms template pack
CRISPY_TEMPLATE_PACK = 'bootstrap3'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(os.path.dirname(BASE_DIR), 'false', 'ts-cache'),
    }
}

REST_FRAMEWORK = {'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema'}
