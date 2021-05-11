"""
Authentication settings for transtats project.
    - this is a temporary placement of OIDC values
    - they should be a part of dev, test only.
"""
from .base import (
    app_config_vars, INSTALLED_APPS, AUTHENTICATION_BACKENDS
)

FAS_AUTH = app_config_vars('TS_AUTH_SYSTEM') == 'fedora'

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('transtats', 'admin@transtats.org'),
)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ADMIN_INITIAL_PASSWORD = app_config_vars('ADMIN_PASSWORD')

# OpenID Connect
# NOTE: This client ID only works on localhost:8080.
INSTALLED_APPS += ('mozilla_django_oidc', 'rest_framework.authtoken')
AUTHENTICATION_BACKENDS += ('transtats.utils.TranstatsOIDCBackend', )
OIDC_RP_CLIENT_ID = app_config_vars('OIDC_RP_CLIENT_ID')
OIDC_RP_CLIENT_SECRET = app_config_vars('OIDC_RP_CLIENT_SECRET')
OIDC_OP_AUTHORIZATION_ENDPOINT = 'https://{0}/openidc/Authorization'.format(app_config_vars('OIDC_BASE_DOMAIN'))
OIDC_OP_TOKEN_ENDPOINT = 'https://{0}/openidc/Token'.format(app_config_vars('OIDC_BASE_DOMAIN'))
OIDC_OP_USER_ENDPOINT = 'https://{0}/openidc/UserInfo'.format(app_config_vars('OIDC_BASE_DOMAIN'))
OIDC_OP_JWKS_ENDPOINT = 'https://{0}/openidc/Jwks'.format(app_config_vars('OIDC_BASE_DOMAIN'))
OIDC_RP_SIGN_ALGO = 'RS256'
LOGOUT_REDIRECT_URL = '/'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
}

if FAS_AUTH:
    CORS_ORIGIN_ALLOW_ALL = True
