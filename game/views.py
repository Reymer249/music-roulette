from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from .models import Parties, UsersParties
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
        return redirect(f"/lobby/{party.pid}/")
    return main_page(request)  # Render the main page with the button


def lobby_page(request, lobby_id):
    user = request.user
    lobbies_with_id = Parties.objects.filter(pid=lobby_id)

    # if the user is not authenticated or if the lobby no longer exists - send to main page
    if not user.is_authenticated or not lobbies_with_id.count():
        return redirect("/")

    lobby = lobbies_with_id.first()

    # count admins in lobby (might be 0)
    is_admin = (UsersParties.objects.filter(party_id=lobby, is_admin=True).count() == 0)
    # create a record in the database that the user joined the lobby
    UsersParties.objects.create(party_id=lobby, user_id=user, is_admin=is_admin)

    return render(request, "lobby_page/index.html", {"lobby_id": lobby_id, "is_admin": is_admin})
