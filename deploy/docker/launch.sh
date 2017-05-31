#!/usr/bin/env bash

cd /workspace
export PYTHONPATH=/workspace;$PYTHONPATH

# setup db
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l logfile start" && sleep 5
sudo -u postgres psql -c "ALTER USER $DATABASE_USER WITH PASSWORD '$DATABASE_PASSWD';"
sudo -u postgres psql -c "CREATE DATABASE $DATABASE_NAME;"
make migrate
su - postgres -c "psql -d $DATABASE_NAME -a -f /workspace/deploy/docker/data/initial.sql"

# setup app
python3 manage.py initlogin && make demo
