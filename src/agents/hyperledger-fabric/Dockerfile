FROM python:3.13

# Install software
RUN apt-get update\
	&& apt-get upgrade

CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
