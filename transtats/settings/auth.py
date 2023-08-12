"""
Authentication settings for transtats project.
    - this is a temporary placement of OIDC values
    - they should be a part of dev, test only.
"""
from .base import (
    app_config_vars, INSTALLED_APPS, AUTHENTICATION_BACKENDS, REST_FRAMEWORK
)

__all__ = [
    'FAS_AUTH',
    'ADMINS',
    'SECURE_PROXY_SSL_HEADER',
    'ADMIN_INITIAL_PASSWORD',
    'INSTALLED_APPS',
    'AUTHENTICATION_BACKENDS',
    'OIDC_RP_CLIENT_ID',
    'OIDC_RP_CLIENT_SECRET',
    'OIDC_OP_AUTHORIZATION_ENDPOINT',
    'OIDC_OP_TOKEN_ENDPOINT',
    'OIDC_OP_USER_ENDPOINT',
    'OIDC_OP_JWKS_ENDPOINT',
    'OIDC_RP_SIGN_ALGO',
    'LOGOUT_REDIRECT_URL',
    'CORS_ORIGIN_ALLOW_ALL',
    'GITHUB_USER',
    'GITHUB_TOKEN'
]

FAS_AUTH = app_config_vars('TS_AUTH_SYSTEM') == 'fedora'

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('transtats', 'admin@transtats.org'),
)

USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ADMIN_INITIAL_PASSWORD = app_config_vars('ADMIN_PASSWORD')

# OpenID Connect
# NOTE: This client ID only works on localhost:8080.
INSTALLED_APPS += ('mozilla_django_oidc', 'rest_framework.authtoken')
OIDC_AUTHENTICATE_CLASS = 'dashboard.views.FedoraAuthRequestView'
AUTHENTICATION_BACKENDS += ('transtats.utils.TranstatsOIDCBackend', )
OIDC_RP_CLIENT_ID = app_config_vars('OIDC_RP_CLIENT_ID')
OIDC_RP_CLIENT_SECRET = app_config_vars('OIDC_RP_CLIENT_SECRET')
OIDC_OP_AUTHORIZATION_ENDPOINT = 'https://{0}/openidc/Authorization'.format(app_config_vars('OIDC_BASE_DOMAIN'))
OIDC_OP_TOKEN_ENDPOINT = 'https://{0}/openidc/Token'.format(app_config_vars('OIDC_BASE_DOMAIN'))
OIDC_OP_USER_ENDPOINT = 'https://{0}/openidc/UserInfo'.format(app_config_vars('OIDC_BASE_DOMAIN'))
OIDC_OP_JWKS_ENDPOINT = 'https://{0}/openidc/Jwks'.format(app_config_vars('OIDC_BASE_DOMAIN'))
OIDC_RP_SIGN_ALGO = 'RS256'
LOGOUT_REDIRECT_URL = '/'

REST_FRAMEWORK.update({
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
})

CORS_ORIGIN_ALLOW_ALL = bool(FAS_AUTH)

GITHUB_USER = "transtats-bot"
GITHUB_TOKEN = app_config_vars('GITHUB_TOKEN')
