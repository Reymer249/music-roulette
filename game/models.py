from django.db import models
from django.contrib.auth.models import AbstractUser


class Users(AbstractUser):
    uid = models.AutoField(primary_key=True)
    username = models.CharField(unique=True)
    spotify_link = models.URLField(max_length=1000, null=False, unique=False)


class Parties(models.Model):
    pid = models.AutoField(primary_key=True)


class UsersParties(models.Model):
    party = models.ForeignKey(Parties, on_delete=models.CASCADE)
    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
