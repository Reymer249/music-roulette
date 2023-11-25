from django import forms
from django.contrib.auth.forms import UserCreationForm
from.models import Users


# class RegisterForm(UserCreationForm):
#     spotify_link = forms.URLField(required=True)
#
#     class Meta:
#         model = Users
#         fields = ["name", "spotify_link", "password1", "password2"]


class LoginForm(forms.ModelForm):
    name = forms.CharField(label="Username", max_length=100)
    spotify_link = forms.URLField(required=True)

    class Meta:
        model = Users
        fields = ["name", "spotify_link"]
