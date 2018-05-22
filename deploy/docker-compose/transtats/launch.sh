#!/usr/bin/env bash

cd /workspace
export PYTHONPATH=/workspace;$PYTHONPATH

# If env variable not set for db values
if [ -z "$DATABASE_USER" ]
then
    echo "Set DB User"
    export DATABASE_USER="postgres"
fi

if [ -z "$DATABASE_PASSWORD" ]
then
    echo "Set DB Password"
    export DATABASE_PASSWORD="postgres"
fi

if [ -z "$DATABASE_NAME" ]
then
    echo "Set DB Name"
    export DATABASE_NAME="transtats"
fi

make static
make migrate
make cache
python3 manage.py loaddata data.json
python3 manage.py initlogin 
python3 manage.py runserver 0:8080 --settings=transtats.settings.test
