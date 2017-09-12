#!/usr/bin/env bash

cd /workspace
export PYTHONPATH=/workspace;$PYTHONPATH

# setup db
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l logfile start" && sleep 5

# If env variable not set for db values
if [ -z "$DATABASE_USER" ]
then
    echo "Set DB User"
    export DATABASE_USER="postgres"
fi

if [ -z "$DATABASE_PASSWD" ]
then
    echo "Set DB Password"
    export DATABASE_PASSWD="postgres"
fi

if [ -z "$DATABASE_NAME" ]
then
    echo "Set DB Name"
    export DATABASE_NAME="transtats"
fi

sudo -u postgres psql -c "ALTER USER $DATABASE_USER WITH PASSWORD '$DATABASE_PASSWD';"
sudo -u postgres psql -c "CREATE DATABASE $DATABASE_NAME;"
make migrate
su - postgres -c "psql -d $DATABASE_NAME -a -f /workspace/deploy/docker/data/initial.sql"

# setup app
python3 manage.py initlogin && make demo
