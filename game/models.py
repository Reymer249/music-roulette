from django.db import models
from django.contrib.auth.models import AbstractUser


class Users(AbstractUser):
    spotify_link = models.CharField(max_length=100, null=False, unique=True)


class Parties(models.Model):
    pid = models.AutoField(primary_key=True)


class UsersParties(models.Model):
    party_id = models.ForeignKey(Parties, on_delete=models.CASCADE)
    user_id = models.OneToOneField(Users, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)


class Messages(models.Model):
    # TODO: handle time of the message so we can filter
    mid = models.AutoField(primary_key=True)
    party_id = models.ForeignKey(Parties, db_column="messages", on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
