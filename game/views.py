from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib.auth import login
from .models import Parties, UsersParties
from django.core.cache import cache
from .forms import LoginForm
from .corlos import get_spotipy_auth_manager
from django.conf import settings
import json
import random
import time


def check_if_authenticated(request):
    user = request.user

    return not (not user.is_authenticated
                or user.spotify_token is None
                or json.loads(user.spotify_token.replace("'", '"'))['expires_at'] < time.time() + 300)


def login_page(request):
    if check_if_authenticated(request):
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
            # redirect to spotify login page
            form.instance.username = f'{random.randrange(1000000000)}'
            user = form.save()
            login(request, user)

            scopes = [
                'user-top-read',
                'user-read-recently-played',
                'user-library-read',
            ]
            scope_string = " ".join(scopes)

            # TODO: redirect to spotify login with callback and pass parameter next
            return redirect(f"https://accounts.spotify.com/authorize"
                     f"?client_id={settings.CLIENT_ID}"
                     f"&redirect_uri={settings.REDIRECT_URI}"
                     f"&response_type=code"
                     f"&scope={scope_string}")
        else:
            context["errors"] = form.errors

    ivan_code = request.GET.get('code')
    if ivan_code:
        if ivan_code == settings.IVAN_CODE:
            request.session['code'] = True

    return HttpResponse(template.render(context, request))


def spotify_callback(request):
    authorization_code = request.GET.get('code')
    auth_manager = get_spotipy_auth_manager()

    # save user token and exp time
    user = request.user
    user.spotify_token = auth_manager.get_access_token(authorization_code)

    user.save()

    level_code = request.session.get('code')
    if level_code is not None:
        user.level = 7

    user.save()

    # Check if 'next' parameter exists in the GET parameters
    next_param = request.session.get('next')

    print(next_param)

    if next_param:
        return redirect(next_param)
    else:
        return redirect(settings.LOGIN_REDIRECT_URL)


def main_page(request):
    if not check_if_authenticated(request):
        return redirect(f"{settings.LOGIN_URL}")

    return render(request, "main_page.html", {})


def create_party(request):
    if not check_if_authenticated(request):
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    # Create a new Parties record
    new_party = Parties()
    new_party.save()

    # Redirect to the lobby page
    return redirect(f"/lobby/{new_party.id}/")


def lobbyselect_page(request):
    if not check_if_authenticated(request):
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    lobby_ids = [lobby.id for lobby in Parties.objects.all()]
    template = loader.get_template("lobbyselect_page.html")
    return HttpResponse(template.render({"lobby_list": lobby_ids}, request))


def lobby_page(request, lobby_id):
    if not check_if_authenticated(request):
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
    if not check_if_authenticated(request):
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    template = loader.get_template("game_page.html")
    return HttpResponse(template.render({"lobby_id": lobby_id}, request))


def results_page(request, lobby_id):
    # get the list of player objects in the lobby
    player_list = [up.user for up in UsersParties.objects.filter(party_id=lobby_id)]

    # get scores from django cache
    scores = cache.get(f"lobby_{lobby_id}_scores")

    score_list = [{"name": player.name, "score": scores[player.id], "level": player.level}
                       for player in player_list]
    score_list_sorted = sorted(score_list, key=lambda x: x["score"], reverse=True)

    for i, player in enumerate(score_list_sorted):
        player["place"] = i + 1

    print(score_list_sorted)

    template = loader.get_template("results_page.html")
    context = {
        "lobby_id": lobby_id,
        "score_list": score_list_sorted
    }
    return HttpResponse(template.render(context, request))
