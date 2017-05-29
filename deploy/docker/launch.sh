#!/usr/bin/env bash

cd /workspace
export PYTHONPATH=/workspace;$PYTHONPATH

# setup db
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l logfile start" && sleep 5
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "CREATE DATABASE transtats;"
make migrate
su - postgres -c "psql -d transtats -a -f /workspace/deploy/docker/data/initial.sql"

# setup app
python3 manage.py initlogin && make demo
