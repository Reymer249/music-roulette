import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from django.conf import settings


SCOPES = [
    'user-top-read',
    'user-read-recently-played',
    'user-library-read',
]

CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET
REDIRECT_URI = settings.REDIRECT_URI


def get_embedded_html(spotify_url):
    response = requests.get('https://open.spotify.com/oembed?url=' + spotify_url)
    if response:    # Meaning code < 400:
        data = response.json()
        return data['html']
    return None


def get_spotipy_auth_manager():
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
    )
    return auth_manager


def get_spotipy_service(token):
    return spotipy.Spotify(auth=token)


def get_top_tracks(service, limit=20, offset=0, time_range='short_term'):
    """
    Return 20 of the most user top tracks.

        param:limit         only goes up to 50, more will fail the request
        param:offset        if you need more than 50 songs, you can use offset=50 to request deeper.
        param:time_range    can also be "medium_term" or "long_term"
    """
    response = service.current_user_top_tracks(limit=limit)
    if not response:
        return None

    total = []
    for track in response['items']:
        summary = {
            'spotify_url': track['external_urls']['spotify'],
            'popularity': track['popularity']
        }
        total.append(summary)

    return total


def get_recent_tracks(service, limit=20, after=None, before=None):
    """
    Returns the 20 most recently played songs from user.

        param:after     unix timestamp in milliseconds
        param:before    unix timestamp in milliseconds

        Only one can be chosen at the same time. They will return
        all recent tracks inside that period.
    """

    response = service.current_user_recently_played(limit=limit)
    if not response:
        return None

    total = []
    for track in response['items']:
        summary = {
            'spotify_url': track['track']['external_urls']['spotify'],
            'popularity': track['track']['popularity']
        }
        total.append(summary)

    return total


def get_saved_tracks(service, limit=20, offset=0):
    """
    Returns the 20 most recent user saved tracks.

        param:limit         only goes up to 50, more will fail the request
        param:offset        if you need more than 50 songs, you can use offset=50 to request deeper.
    """
    resp = service.current_user_saved_tracks(limit=limit)
    if not resp:
        return None

    total = []
    for track in resp['items']:
        summary = {
            'spotify_url': track['track']['external_urls']['spotify'],
            'popularity': track['track']['popularity']
        }
        total.append(summary)

    return total
