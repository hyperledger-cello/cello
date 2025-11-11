#!/usr/bin/bash

holdup -t 120 tcp://${DB_HOST:-localhost}:${DB_PORT:-5432};
python manage.py migrate;
python manage.py collectstatic
DEBUG="${DEBUG:-True}"
if [[ "${DEBUG,,}" == "true" ]]; then # For dev, use pure Django directly
  python manage.py runserver 0.0.0.0:8080;
else # For production, use uwsgi in front
  uwsgi --ini server.ini;
fi
