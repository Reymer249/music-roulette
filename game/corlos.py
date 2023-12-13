from dotenv import load_dotenv
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cacha_handler import DjangoSessionCacheHandler

import requests
import webbrowser
import base64
from urllib.parse import urlencode

load_dotenv()   # This loads variables from .env as environmental variables.

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

SCOPES = [
  # 'playlist-read-collaborative', 
    'user-top-read', 
    'user-read-recently-played',
    'user-library-read',
    ]


def get_embedded_html(spotify_url):
    response = requests.get('https://open.spotify.com/oembed?url=' + spotify_url)
    if response:    # Meaning code < 400:
        data = response.json()
        return data['html']
    return None
   
 
def get_spotipy_auth_manager():
    auth_manager = SpotifyOAuth(   
                    client_id = CLIENT_ID,
                    client_secret = CLIENT_SECRET,
                    redirect_uri = REDIRECT_URI,
                    scope = SCOPES,
                    )
    return auth_manager


def get_spotipy_service(token):
    return spotipy.Spotify(auth=token)


def get_top_tracks(service, *, limit=20, offset=0, time_range='short_term'):
    ''' 
    Return 20 of the most user top tracks. 
        
        param:limit         only goes up to 50, more will fail the request
        param:offset        if you need more than 50 songs, you can use offset=50 to request deeper. 
        param:time_range    can also be "medium_term" or "long_term" 
    ''' 
    response = service.current_user_top_tracks(limit=limit, offset=offset, time_range=time_range)
    if not response:
        return None

    total = []
    for track in response['items']:
        summary = {
            'duration_sec': int(track['duration_ms'] * 1000),
            'popularity': track['popularity'],
            'spotify_url': track['external_url']['spotify'],
        }
        total.append(summary)

    return total


def get_recent_tracks(service, *, limit=20, after=None, before=None):
    '''
    Returns the 20 most recently played songs from user.

        param:after     unix timestamp in milliseconds
        param:before    unix timestamp in milliseconds

        Only one can be chosen at the same time. They will return
        all recent tracks inside that period. 
    '''
    response = service.current_user_recently_played(limit=limit, offset=offset, time_range=time_range)
    if not response:
        return None

    total = []
    for track in response['items']:
        summary = {
            'duration_sec': int(track['duration_ms'] * 1000),
            'popularity': track['popularity'],
            'spotify_url': track['external_url']['spotify'],
        }
        total.append(summary)

    return total


def get_saved_tracks(service, *, limit=20, offset=0):
    '''
    Returns the 20 most recent user saved tracks.

        param:limit         only goes up to 50, more will fail the request
        param:offset        if you need more than 50 songs, you can use offset=50 to request deeper. 
    '''
    resp = service.current_user_saved_tracks(limit=limit, offset=offset)
    if not response:
        return None

    total = []
    for item in resp['items']:
        track = item['track']
        summary = {
            'duration_sec': int(track['duration_ms'] * 1000),
            'popularity': track['popularity'],
            'preview_url': track['preview_url'],
        }
        total.append(summary)

    return total

