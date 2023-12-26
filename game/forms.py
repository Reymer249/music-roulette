from django import forms
from django.contrib.auth.forms import UserCreationForm
from.models import Users


class LoginForm(forms.ModelForm):
    name = forms.CharField(label="Username", max_length=30)

    class Meta:
        model = Users
        fields = ["name"]
