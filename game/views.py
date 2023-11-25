from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from .models import Parties, UsersParties, Users
from .forms import LoginForm
import random


def login_page(request):
    if request.user.is_authenticated:
        return redirect("/main-page")

    template = loader.get_template("login_page/index.html")
    context = {
        "form": LoginForm(),
        "errors": None
    }

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            form.instance.username = f'{random.randrange(1000000000)}'
            user = form.save()
            login(request, user)
            return redirect("/main-page")
        else:
            context["errors"] = form.errors

    return HttpResponse(template.render(context, request))


def main_page(request):
    if not request.user.is_authenticated:
        return redirect("/")
    return render(request, "main_page/index.html", {})


def create_party(request):
    if not request.user.is_authenticated:
        return redirect("/")

    # Create a new Parties record
    new_party = Parties()
    new_party.save()

    # Redirect to the lobby page
    return redirect(f"/lobby/{new_party.id}/")

def lobbyselect_page(request):
    if not request.user.is_authenticated:
        return redirect("/")

    lobby_ids = [lobby.id for lobby in Parties.objects.all()]
    template = loader.get_template("lobbyselect_page/index.html")
    context = {"lobby_list": lobby_ids}
    return HttpResponse(template.render(context, request))


def lobby_page(request, lobby_id):
    if not request.user.is_authenticated:
        return redirect("/")

    user = request.user
    UsersParties.objects.filter(user=user).delete()

    # Create a new UsersParties record
    parties = Parties.objects.filter(id=lobby_id)
    # check whether party exists DO NOT TOUCH MAX
    if not parties.count():
        return redirect("/")
    party = parties[0]
    is_admin = (len(UsersParties.objects.filter(party=party)) == 1)
    user_party = UsersParties(
        party=party,
        user=user,
        is_admin=is_admin
    )
    user_party.save()

    # Get names of the players in the party
    player_list = Users.objects.filter(usersparties__party=party.id).values('name')
    template = loader.get_template("lobby_page/index.html")
    context = {
        "lobby_id": lobby_id,
        "user_party": user_party,
    }
    return HttpResponse(template.render(context, request))

def question_page(request, lobby_id):
    if not request.user.is_authenticated:
        return redirect("/")
    player_list = [{"id": 11, "name": "Natalka"}, {"id": 12, "name": "Ivan"}, {"id": 13, "name": "Max"}, {"id": 14, "name": "Carlos"}]
    template = loader.get_template("question_page/index.html")
    context = {
        "lobby_id": lobby_id,
        "player_list": player_list,
        "num_players": len(player_list),
    }
    return HttpResponse(template.render(context, request))

def results_page(request, lobby_id):
    if not request.user.is_authenticated:
        return redirect("/")
    player_list = [{"id": 11, "name": "Natalka"}, {"id": 12, "name": "Ivan"}, {"id": 13, "name": "Max"}, {"id": 14, "name": "Carlos"}]
    result_list = [{"id": 11, "points": 100}, {"id": 12, "points": 90}, {"id": 13, "points": 80}, {"id": 14, "points": 70}]
    template = loader.get_template("results_page/index.html")
    context = {
        "lobby_id": lobby_id,
        "player_list": player_list,
        "result_list": result_list,
        "num_players": len(player_list),
    }
    return HttpResponse(template.render(context, request))
