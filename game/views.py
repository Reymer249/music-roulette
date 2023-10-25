from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from .models import Parties
from .forms import RegisterForm


def main_page(request):
    lobby_ids = [lobby.pid for lobby in Parties.objects.all()]
    return render(request, "main_page/index.html", {"lobby_list": lobby_ids, "user": request.user})


def sign_up(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = RegisterForm()

    return render(request, "registration/sign_up.html", {"form": form})


def create_party(request):
    if request.method == "POST":
        # Create a new Parties record
        party = Parties.objects.create()
        # Redirect to the lobby page
        return lobby_page(request, party.pid)
    return main_page(request)  # Render the main page with the button


def lobby_page(request, lobby_id):
    return render(request, "lobby_page/index.html", {"lobby_id": lobby_id})
