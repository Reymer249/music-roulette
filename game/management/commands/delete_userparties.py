from django.core.management.base import BaseCommand
from game.models import Parties


class Command(BaseCommand):
    def handle(self, *args, **options):
        Parties.objects.all().delete()
        print("Deleted all party records")
