from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from .models import Parties, UsersParties
from .forms import RegisterForm


def login_page(request):
    template = loader.get_template("login_page/index.html")
    context = {
        "i": 1,
    }
    return HttpResponse(template.render(context, request))

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

def lobbyselect_page(request):
    lobby_list = [{"id": 12345}, {"id": 54321}, {"id": 23576}, {"id": 79840}]
    template = loader.get_template("lobbyselect_page/index.html")
    context = {
        "lobby_list": lobby_list,
    }
    return HttpResponse(template.render(context, request))

def lobby_page(request, lobby_id):
    player_list = [{"id": 11, "name": "Natalka"}, {"id": 12, "name": "Ivan"}, {"id": 13, "name": "Max"}, {"id": 14, "name": "Carlos"}]
    template = loader.get_template("lobby_page/index.html")
    context = {
        "lobby_id": lobby_id,
        "player_list": player_list,
        "num_players": len(player_list),
    }
    return HttpResponse(template.render(context, request))

def question_page(request, lobby_id):
    player_list = [{"id": 11, "name": "Natalka"}, {"id": 12, "name": "Ivan"}, {"id": 13, "name": "Max"}, {"id": 14, "name": "Carlos"}]
    template = loader.get_template("question_page/index.html")
    context = {
        "lobby_id": lobby_id,
        "player_list": player_list,
        "num_players": len(player_list),
    }
    return HttpResponse(template.render(context, request))

def results_page(request, lobby_id):
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
