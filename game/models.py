from django.db import models
from django.contrib.auth.models import AbstractUser


class Users(AbstractUser):
    name = models.CharField(unique=False)
    spotify_token = models.CharField(max_length=1000, null=True)
    spotify_token_exp = models.FloatField(null=True)


class Parties(models.Model):
    pass


class UsersParties(models.Model):
    party = models.ForeignKey(Parties, on_delete=models.CASCADE)
    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
