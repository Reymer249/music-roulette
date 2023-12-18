#!/bin/bash

python manage.py makemigrations game

python manage.py migrate

python manage.py createcachetable

celery -A musicroulette purge -f

python manage.py delete_userparties

celery -A musicroulette worker -l info -P solo &

python manage.py runserver 0.0.0.0:8000 &

wait -n

exit $?
