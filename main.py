from dotenv import load_dotenv
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotipy classes are able to get env variables on their own, either way I insist on passing it manually.

load_dotenv()   # This loads variables from .env as environmental variables.

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

SCOPES = [
    'user-read-playback-state', 
    'user-modify-playback-state', 
  # 'user-read-currently-playing',  # Possibly redundant with 'user-read-playback-state'
  # 'app-remote-control',   # Regards iOS and Android SDK
    'streaming',            # Interacts with Web Playback SDK
  # 'playlist-read-private',    # I don't think we should read private playlists. (Not even set option to) 
    'playlist-read-collaborative', 
    'user-top-read', 
    'user-read-recently-played',
    'user-library-read',
    ]


oauth = SpotifyOAuth(   
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES
            )
 
spotify = spotipy.Spotify(oauth_manager=oauth)


def get_saved_tracks(service, limit=50, offset=0):

    resp = service.current_user_saved_tracks(limit=limit, offset=offset)
    total = []
    for item in resp['items']:
        track = item['track']
        summary = {
            'album_name': track['album']['name'],
            'artist_names': [artist_resp['name'] for artist_resp in track['artists']],
            'duration_sec': int(track['duration_ms'] * 1000),
            'name': track['name'],
            'popularity': track['popularity'],
            'preview_url': track['preview_url'],
        }
        total.append(summary)

    return total



def get_top_tracks(service, limit=50, offset=0, time_range='medium_term'):
    '''Time range varies from: "short_term", "medium_term" and "long_term". '''    
    resp = service.current_user_top_tracks(limit=limit, offset=offset, time_range=time_range)
    total = []
    for track in resp['items']:
        summary = {
            'album_name': track['album']['name'],
            'artist_names': [artist_resp['name'] for artist_resp in track['artists']],
            'duration_sec': int(track['duration_ms'] * 1000),
            'name': track['name'],
            'popularity': track['popularity'],
            'preview_url': track['preview_url'],
        }
        total.append(summary)

    return total



def get_all_tracks(service, getter_func, limit=500):
    offset = 0
    total = []
    while len(total) == offset and len(total) < limit:
        total += getter_func(service, offset=offset)
        offset += 50
    
    return total[:limit]



if __name__ == '__main__':

    # Some test code with meaning

    oauth = SpotifyOAuth(   
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope=SCOPES
                )
     
    spotify = spotipy.Spotify(oauth_manager=oauth)

    names = []

    for time_range in ['short_term', 'medium_term', 'long_term']:
        custom = lambda service, offset: get_top_tracks(service=service, offset=offset, time_range=time_range)  
        
        resp = get_all_tracks(spotify, custom)
        names.append({track['name'] for track in resp})

    print('Below is a comparison between the different time periods of your top tracks:')
    print(f'Long - medium = {len(names[2] - names[1])} different songs!')
    print(f'Long - short = {len(names[2] - names[0])} different songs!')
    print(f'Medium - short = {len(names[1] - names[0])} different songs!')
    print('These numbers show you how much your music preferences have changed recently.\n')
    print('The following songs have been with you for a while now: (in all 3 periods)')
    print('\n'.join(set.intersection(*names)))






    
