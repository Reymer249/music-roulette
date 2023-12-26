from django.core.management.base import BaseCommand
from game.models import Parties, Users, UsersParties


class Command(BaseCommand):
    def handle(self, *args, **options):
        Parties.objects.all().delete()
        Users.objects.all().delete()
        UsersParties.objects.all().delete()
        print("Deleted all records")
