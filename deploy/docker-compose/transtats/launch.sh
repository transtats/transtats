#!/usr/bin/env bash

set -e
cd /workspace
export PYTHONPATH=/workspace:$PYTHONPATH

if [ -z "$DJANGO_SECRET_KEY" ]
then
    echo "DJANGO_SECRET_KEY is not set. Using default value."
    export DJANGO_SECRET_KEY="111ioii2!n7dv+p@kq905a1m7zs7%_5%j9zw@%8qw20z&*k+b_"
fi

if [ -z "$OIDC_BASE_DOMAIN" ]
then
    echo "OIDC_BASE_DOMAIN is not set. Using default value."
    export OIDC_BASE_DOMAIN="iddev.fedorainfracloud.org"
fi

if [ -z "$OIDC_RP_CLIENT_ID" ]
then
    echo "OIDC_RP_CLIENT_ID is not set. Using default value."
    export OIDC_RP_CLIENT_ID="transtatsdev"
fi

if [ -z "$OIDC_RP_CLIENT_SECRET" ]
then
    echo "OIDC_RP_CLIENT_SECRET is not set. Using default value."
    export OIDC_RP_CLIENT_SECRET="uvwFVN7SNgmNCQVJTR9QdrkMginl0RM4"
fi

if [ -z "$TS_AUTH_SYSTEM" ]
then
    echo "TS_AUTH_SYSTEM is not set. Using Fedora login as default method."
    export TS_AUTH_SYSTEM="fedora"
fi

if [ -z "$ADMIN_PASSWORD" ]
then
    echo "ADMIN_PASSWORD is not set. Using '321@transtats' as default value."
    export ADMIN_PASSWORD="321@transtats"
fi

if [ -z "$DATABASE_HOST" ]
then
    echo "DATABASE_HOST is not set. Using 'localhost' as default."
    export DATABASE_HOST="localhost"
fi

if [ -z "$DATABASE_USER" ]
then
    echo "DATABASE_USER is not set. Using 'postgres' as default value."
    export DATABASE_USER="postgres"
fi

if [ -z "$DATABASE_PASSWORD" ]
then
    echo "DATABASE_PASSWORD is not set. Using 'postgres' as default value."
    export DATABASE_PASSWORD="postgres"
fi

if [ -z "$DATABASE_NAME" ]
then
    echo "DATABASE_HOST is not set. Using 'transtats' as default value."
    export DATABASE_NAME="transtats"
fi

if [ -z "$GUNICORN_CMD_ARGS" ]
then
    echo "GUNICORN_CMD_ARGS is not set. Using default settings."
    export GUNICORN_CMD_ARGS="--workers 3 --bind 0.0.0.0:8080 --timeout 300"
fi

# set environment
make static
make migrate
python3 manage.py initlogin

# start celery to run tasks
redis-server &
celery -A transtats worker -l info -f transtats/logs/celery/transtats_worker.log &
celery -A transtats beat -l info --pidfile run/celerybeat.pid -s run/celerybeat-schedule -f transtats/logs/celery/transtats_beat.log &

# launch application
gunicorn transtats.wsgi:application
