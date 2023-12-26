#!/bin/bash
source .env

if [ "$LOCAL_DEV" == "True" ]; then
    echo "Running in local development mode"
else
    echo "Running on production"
    sleep 20
fi

python manage.py makemigrations game

python manage.py migrate

python manage.py createcachetable

celery -A musicroulette purge -f

python manage.py delete_userparties

celery -A musicroulette worker -l info &

python manage.py runserver 0.0.0.0:80 &

wait -n

exit $?
