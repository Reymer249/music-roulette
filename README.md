# Music Roulette
Music Roulette is a web game you may play with your friends during the party. It goes simple: the tracks are playing one-by-one and for each of them you have to guess from whose playlist is it.

How to start the server for local testing/development:
1) start your local postgreSQL database server
2) start your local Redis database server
3) you might want to delete the unfinished Celery tasks (celery -A musicroulette purge)
4) start Celery (celery -A musicroulette worker -l info -P solo)
5) delete existing party records (python manage.py delete_userparties)
(Because when django server stops unexpectedly - the user-parties database isn't erased, so next time you launch django it assumes you are already in a party and throws an error)
6) start Django (python manage.py runserver)