#!/usr/bin/bash

python manage.py migrate
python manage.py collectstatic --noinput
DEBUG="${DEBUG:-True}"
if [[ "${DEBUG,,}" == "true" ]]; then # For dev, use pure Django directly
  python manage.py runserver 0.0.0.0:8080
else # For production, use uwsgi in front
  uwsgi --ini server.ini
fi
