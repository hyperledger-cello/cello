#!/usr/bin/env bash

holdup -t 120 tcp://${DB_HOST:-localhost}:${DB_PORT:-5432};
python manage.py migrate;
python manage.py create_user \
  --username ${API_ENGINE_ADMIN_EMAIL:-admin@cello.com} \
  --password ${API_ENGINE_ADMIN_PASSWORD:-pass} \
  --email ${API_ENGINE_ADMIN_EMAIL:-admin@cello.com} \
  --is_superuser \
  --role admin
if [[ "${DEBUG:-True,,}" == "true" ]]; then # For dev, use pure Django directly
  python manage.py runserver 0.0.0.0:8080;
else # For production, use uwsgi in front
  uwsgi --ini server.ini;
fi
