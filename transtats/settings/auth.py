"""
Authentication settings for transtats project.
    - this is a temporary placement of OIDC values
    - they should be a part of dev, test only.
"""
from .base import (
    app_config_vars, INSTALLED_APPS, AUTHENTICATION_BACKENDS
)

FAS_AUTH = app_config_vars('TS_AUTH_SYSTEM')

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('transtats', 'transtats@example.com'),
)

# OpenID Connect
# NOTE: This client ID only works on localhost:8080.
INSTALLED_APPS += ('mozilla_django_oidc', )
AUTHENTICATION_BACKENDS += ('transtats.utils.TranstatsOIDCBackend', )
OIDC_RP_CLIENT_ID = 'transtatsdev'
OIDC_RP_CLIENT_SECRET = app_config_vars('OIDC_RP_CLIENT_SECRET')
OIDC_OP_AUTHORIZATION_ENDPOINT = 'https://iddev.fedorainfracloud.org/openidc/Authorization'
OIDC_OP_TOKEN_ENDPOINT = 'https://iddev.fedorainfracloud.org/openidc/Token'
OIDC_OP_USER_ENDPOINT = 'https://iddev.fedorainfracloud.org/openidc/UserInfo'
OIDC_RP_SIGN_ALGO = 'RS256'
# fix OIDC_RP_IDP_SIGN_KEY to use latest mozilla-django-oidc
OIDC_RP_IDP_SIGN_KEY = {"use": "sig", "kid": "1462960685-sig", "e": "AQAB", "kty": "RSA", "n": "q_0_XjILQxF3OaQZtFE3wVJ5UUuxZbxiJ_z-Zai0EOHiaMMxVyooibDRen615r525DQ8TmQyR0eMQEpQ6SUvaOunahpYohgAkbkYggUMQhcoCLme18ZJBTNWTP8w4t7mcuZd1cy1KtHpEvH4gkrjp8N3vIv1lzFraSc-p2rHMbV-AX5CJQ1HohBdwaqyOBKp0nzY27gu2EH2vzCwXkO4zGtrHfjjGc0Ra4WG-xz1AWg833xcFj3pqM3vca09jDLBme-GT151LcCCXRNyOZPZ3ZX62NxkMyqvVJHC3Uu2Q1hSHO7f6AZkZXY88PXXEH52T2ZrWiISowjTcGUboP8goQ"}
LOGOUT_REDIRECT_URL = '/'
