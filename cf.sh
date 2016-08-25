#!/bin/bash
echo "------ Starting APP ------"
if [ $CF_INSTANCE_INDEX = "0" ]; then
    echo "----- Migrating Database -----"
    python manage.py migrate --noinput
    echo "----- Loading Labor Category Data -----"
    python manage.py load_data
    python manage.py load_s70
fi
newrelic-admin run-program gunicorn hourglass.wsgi:application
