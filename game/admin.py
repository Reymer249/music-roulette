from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Users)
admin.site.register(Parties)
admin.site.register(UsersParties)
admin.site.register(Messages)
