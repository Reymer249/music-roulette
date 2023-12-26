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
from spotipy.oauth2 import SpotifyOAuth


CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET
REDIRECT_URI = settings.REDIRECT_URI


def check_if_authenticated(request):
    """
    This function checks if the user is authenticated.

    Parameters:
    request (HttpRequest): The request object.

    Returns:
    bool: True if the user is authenticated, False otherwise.
    """
    user = request.user

    try:
        print(f"{user.name}: {user.spotify_token}")
    except:
        print("no name / token")

    return not (not user.is_authenticated
                or user.spotify_token is None
                or json.loads(user.spotify_token.replace("'", '"'))['expires_at'] < time.time() + 300)


def login_page(request):
    """
    This function handles the login page. It checks if the user is authenticated and if so, redirects them to the next page or the default login redirect URL.
    If the user is not authenticated, it loads the login page template and handles the POST request if the form is submitted.
    If the form is valid, it redirects the user to the Spotify login page.
    If the form is not valid, it adds the form errors to the context.
    It also checks if the 'code' GET parameter is equal to the IVAN_CODE setting and if so, sets the 'code' session variable to True.

    Parameters:
    request (HttpRequest): The request object.

    Returns:
    HttpResponse: The HTTP response.
    """
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
    """
    This function is the callback for the Spotify authorization process. It is called when Spotify redirects the user back to our application after successful authorization.
    It retrieves the authorization code from the GET parameters, and uses it to get an access token from Spotify.
    The access token is then saved in the user's profile for future API calls.
    If the user has a 'code' in their session, their level is set to 7.
    Finally, the function checks if there is a 'next' parameter in the session. If it exists, the user is redirected to that URL. Otherwise, they are redirected to the LOGIN_REDIRECT_URL.
    """
    authorization_code = request.GET.get('code')
    auth_manager = get_spotipy_auth_manager()

    # save user token and exp time
    user = request.user
    user.spotify_token = auth_manager.get_access_token(authorization_code, check_cache=False)

    level_code = request.session.get('code')
    if level_code:
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
    """
    This function handles the main page of the application.
    It first checks if the user is authenticated. If not, it redirects the user to the login page.
    If the user is authenticated, it renders the main page of the application.
    """
    if not check_if_authenticated(request):
        return redirect(f"{settings.LOGIN_URL}")

    return render(request, "main_page.html", {})


def create_party(request):
    """
    This function handles the creation of a new party.

    It first checks if the user is authenticated. If not, it redirects the user to the login page.
    If the user is authenticated, it creates a new Parties record and saves it.
    Finally, it redirects the user to the lobby page of the newly created party.

    Parameters:
    request (HttpRequest): The request object.

    Returns:
    HttpResponse: A redirect response to the lobby page of the newly created party.
    """
    if not check_if_authenticated(request):
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    # Create a new Parties record
    new_party = Parties()
    new_party.save()

    # Redirect to the lobby page
    return redirect(f"/lobby/{new_party.id}/")


def lobbyselect_page(request):
    """
    This function handles the lobby selection page.

    It first checks if the user is authenticated. If not, it redirects the user to the login page.
    If the user is authenticated, it retrieves all the lobby ids from the Parties model and passes them to the template.
    Finally, it renders the lobby selection page with the list of lobby ids.

    Parameters:
    request (HttpRequest): The request object.

    Returns:
    HttpResponse: The HTTP response with the rendered lobby selection page.
    """
    if not check_if_authenticated(request):
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    lobby_ids = [lobby.id for lobby in Parties.objects.all()]
    template = loader.get_template("lobbyselect_page.html")
    return HttpResponse(template.render({"lobby_list": lobby_ids}, request))


def lobby_page(request, lobby_id):
    """
    This function handles the lobby page.

    It first checks if the user is authenticated. If not, it redirects the user to the login page.
    If the user is authenticated, it deletes any existing UsersParties record for the user.
    Then, it checks if the party with the given lobby_id exists. If not, it redirects the user to the home page.
    If the party exists, it creates a new UsersParties record for the user and the party.
    It also determines if the user is the admin of the party based on whether there are any other UsersParties records for the party with is_admin=True.
    Finally, it renders the lobby page with the lobby_id and whether the user is the admin.

    Parameters:
    request (HttpRequest): The request object.
    lobby_id (int): The id of the lobby.

    Returns:
    HttpResponse: The HTTP response with the rendered lobby page.
    """
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
    """
    This function handles the game page.

    It first checks if the user is authenticated. If not, it redirects the user to the login page.
    If the user is authenticated, it renders the game page with the lobby_id.

    Parameters:
    request (HttpRequest): The request object.
    lobby_id (int): The id of the lobby.

    Returns:
    HttpResponse: The HTTP response with the rendered game page.
    """
    if not check_if_authenticated(request):
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    template = loader.get_template("game_page.html")
    return HttpResponse(template.render({"lobby_id": lobby_id}, request))


def results_page(request, lobby_id):
    """
    This function handles the results page.

    It first retrieves the list of player objects in the lobby. Then, it gets the scores from the Django cache.
    It creates a list of dictionaries, each containing the name, score, and level of a player.
    The list is sorted in descending order of scores. The place of each player in the sorted list is added to their respective dictionary.
    The sorted list is then printed and passed to the template for rendering.

    Parameters:
    request (HttpRequest): The request object.
    lobby_id (int): The id of the lobby.

    Returns:
    HttpResponse: The HTTP response with the rendered results page.
    """
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
