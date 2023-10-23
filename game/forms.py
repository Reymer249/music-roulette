from django import forms
from django.contrib.auth.forms import UserCreationForm
from.models import Users


class RegisterForm(UserCreationForm):
    spotify_link = forms.URLField(required=True)

    class Meta:
        model = Users
        fields = ["username", "spotify_link", "password1", "password2"]
