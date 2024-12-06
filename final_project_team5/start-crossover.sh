#!/bin/bash

#RUN MAKEMIGRATIONS LOCALLY

python manage.py migrate
python manage.py createsuperuser --noinput #it uses the env vars found in dockerfile to make superuser with --noinput
python manage.py runserver 0.0.0.0:8000