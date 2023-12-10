#!/bin/bash

python manage.py makemigrations game

python manage.py migrate

python manage.py createcachetable

celery -A musicroulette purge -f

celery -A musicroulette worker --detach -l info -P solo

python manage.py delete_userparties

python manage.py runserver 0.0.0.0:8000
