#!/usr/bin/env bash

#bash /scripts/initial.sh;

echo "Generating the settings.py for api_engine"
LOCAL_SETTINGS="/var/www/server/api_engine/settings.py"
RAW_LOCAL_SETTINGS="/var/www/server/api_engine/settings.py.example"

envsubst < ${RAW_LOCAL_SETTINGS} > ${LOCAL_SETTINGS}

holdup -t 120 tcp://${DB_HOST}:${DB_PORT};
if [[ "$RUN_MODE" == "server" ]]; then
  python manage.py migrate;
  python manage.py create_user \
    --username ${API_ENGINE_ADMIN_USERNAME:-admin} \
    --password ${API_ENGINE_ADMIN_PASSWORD:-pass} \
    --email ${API_ENGINE_ADMIN_EMAIL:-admin@cello.com} \
    --is_superuser \
    --role admin
  if [[ "$DEBUG" == "True" ]]; then # For dev, use pure Django directly
    python manage.py runserver 0.0.0.0:8080;
  else # For production, use uwsgi in front
    uwsgi --ini /etc/uwsgi/apps-enabled/server.ini;
  fi
else
  celery -A api_engine worker -l info
fi
