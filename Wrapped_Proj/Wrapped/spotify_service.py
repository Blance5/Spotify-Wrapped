# myapp/spotify_service.py
import requests
from decouple import config
from base64 import b64encode

SPOTIFY_CLIENT_ID = config('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = config('SPOTIFY_CLIENT_SECRET')
SCOPES = "user-top-read playlist-read-private user-library-read user-read-email"

def get_spotify_access_token():
    client_creds = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    encoded_creds = b64encode(client_creds.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_creds}"
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    token_info = response.json()
    return token_info.get("access_token")


def get_spotify_data(request):
    access_token = request.session.get('spotify_token')
    if not access_token:
        return {"error": "No access token"}

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        # Retrieve user profile data
        user_profile_response = requests.get("https://api.spotify.com/v1/me", headers=headers)
        if user_profile_response.status_code != 200:
            print("User Profile Error:", user_profile_response.status_code, user_profile_response.text)
            raise Exception("Failed to fetch user profile")

        user_profile = user_profile_response.json()

        # Retrieve top tracks
        top_tracks_response = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=6", headers=headers)
        top_tracks = [
            {
                'name': track['name'],
                'artist': track['artists'][0]['name']
            }
            for track in top_tracks_response.json().get('items', [])
        ] if top_tracks_response.status_code == 200 else []

        # Retrieve top artists
        top_artists_response = requests.get("https://api.spotify.com/v1/me/top/artists?limit=5", headers=headers)
        top_artists = [
            {
                'name': artist['name'],
                'image_url': artist['images'][0]['url'] if artist['images'] else None
            }
            for artist in top_artists_response.json().get('items', [])
        ] if top_artists_response.status_code == 200 else []

        # Retrieve playlists
        playlists_response = requests.get("https://api.spotify.com/v1/me/playlists?limit=5", headers=headers)
        playlists = [
            {
                'name': playlist['name'],
                'description': playlist.get('description', ''),
                'track_count': playlist['tracks']['total']
            }
            for playlist in playlists_response.json().get('items', [])
        ] if playlists_response.status_code == 200 else []

        # Retrieve saved albums
        saved_albums_response = requests.get("https://api.spotify.com/v1/me/albums?limit=5", headers=headers)
        saved_albums = [
            {
                'name': album['album']['name'],
                'artist': album['album']['artists'][0]['name']
            }
            for album in saved_albums_response.json().get('items', [])
        ] if saved_albums_response.status_code == 200 else []

        return {
            'display_name': user_profile.get('display_name', 'User'),
            'email': user_profile.get('email', ''),
            'country': user_profile.get('country', ''),
            'product': user_profile.get('product', ''),
            'top_tracks': top_tracks,
            'top_artists': top_artists,
            'playlists': playlists,
            'saved_albums': saved_albums
        }
    except Exception as e:
        print("Error fetching Spotify data:", e)
        return {"error": "Failed to retrieve Spotify data"}
