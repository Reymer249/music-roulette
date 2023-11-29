from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib.auth import login
from .models import Parties, UsersParties
from .forms import LoginForm
import random


def login_page(request):
    if request.user.is_authenticated:
        # Check if 'next' parameter exists in the GET parameters
        next_param = request.GET.get('next')

        if next_param:
            return redirect(next_param)
        else:
            return redirect(settings.LOGIN_REDIRECT_URL)

    template = loader.get_template("login_page.html")
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

            # Check if 'next' parameter exists in the GET parameters
            next_param = request.GET.get('next')

            if next_param:
                return redirect(next_param)
            else:
                return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            context["errors"] = form.errors

    return HttpResponse(template.render(context, request))


def main_page(request):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}")

    return render(request, "main_page.html", {})


def create_party(request):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    # Create a new Parties record
    new_party = Parties()
    new_party.save()

    # Redirect to the lobby page
    return redirect(f"/lobby/{new_party.id}/")


def lobbyselect_page(request):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    lobby_ids = [lobby.id for lobby in Parties.objects.all()]
    template = loader.get_template("lobbyselect_page.html")
    return HttpResponse(template.render({"lobby_list": lobby_ids}, request))


def lobby_page(request, lobby_id):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    user = request.user
    UsersParties.objects.filter(user=user).delete()

    parties = Parties.objects.filter(id=lobby_id)
    # check whether party exists DO NOT TOUCH MAX
    if not parties.count():
        return redirect("/")

    # create a new UsersParties record
    party = parties[0]
    is_admin = (UsersParties.objects.filter(party=party, is_admin=True).count() == 0)
    user_party = UsersParties(
        party=party,
        user=user,
        is_admin=is_admin
    )
    user_party.save()

    # get names of the players in the party
    template = loader.get_template("lobby_page.html")
    return HttpResponse(template.render({"lobby_id": lobby_id, "is_admin": is_admin}, request))


def game_page(request, lobby_id):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    template = loader.get_template("game_page.html")
    return HttpResponse(template.render({"lobby_id": lobby_id}, request))


def results_page(request, lobby_id):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    player_list = [{"id": 11, "name": "Natalka"}, {"id": 12, "name": "Ivan"},
                   {"id": 13, "name": "Max"}, {"id": 14, "name": "Carlos"}]
    result_list = [{"id": 11, "points": 100}, {"id": 12, "points": 90},
                   {"id": 13, "points": 80}, {"id": 14, "points": 70}]
    template = loader.get_template("results_page.html")
    context = {
        "lobby_id": lobby_id,
        "player_list": player_list,
        "result_list": result_list,
        "num_players": len(player_list),
    }
    return HttpResponse(template.render(context, request))
