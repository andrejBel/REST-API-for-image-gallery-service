#! /bin/bash

while true; do
	echo "restaring django server"
	python3 ./manage.py runserver 0.0.0.0:8000
	# gunicorn --bind :8000 --workers 2 --timeout 30 restapiproject.wsgi:application
	sleep 2;
done
