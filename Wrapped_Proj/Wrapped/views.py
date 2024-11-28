# home/views.py
from django.shortcuts import render
from allauth.account.views import EmailView
from allauth.account.views import LogoutView
from django.views.generic import TemplateView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .spotify_service import get_spotify_data
import requests
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
import urllib.parse
from decouple import config
from django.contrib.auth import login, get_user_model

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_CLIENT_ID = config('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = config('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8000/spotify/callback/"
SPOTIFY_USER_PROFILE_URL = "https://api.spotify.com/v1/me"
SCOPES = "user-top-read playlist-read-private user-library-read user-read-email"

#def home_view(request):
 #   return redirect(request, 'home.html')

def spotify_login(request):
    #request.session.flush()
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
        "show_dialog": "true",
    }
    url_params = urllib.parse.urlencode(params)
    return redirect(f"{auth_url}?{url_params}")


def spotify_callback(request):
    request.session.set_expiry(0)  # Session expires on browser close

    code = request.GET.get('code')
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=data)
    token_info = response.json()

    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")  # Retrieve refresh token
    granted_scopes = token_info.get("scope", "")  # Retrieves granted scopes as a string

    # Log the granted scopes
    print("Granted Scopes:", granted_scopes)
    if access_token and refresh_token:
        # Store tokens in the session
        request.session['spotify_token'] = access_token
        request.session['spotify_refresh_token'] = refresh_token
        request.session['is_authenticated'] = True
        print("Access token stored in session:", access_token)  # Debugging line

        User = get_user_model()
        user, created = User.objects.get_or_create(username="spotify_user")
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('home_logged_in')
    else:
        print("Failed to obtain access or refresh token:", token_info)  # Debugging line   
    return redirect('home_logged_out')


# View for logged in users
#@login_required  # Ensures only logged in users can access this view
def home_logged_in(request):
    if not request.user.is_authenticated or 'spotify_token' not in request.session:
        return redirect('spotify_login')

    access_token = request.session.get('spotify_token')
    if not access_token:
        return redirect('spotify_login')

    try:
        spotify_user_data = get_spotify_data(request)
        print("Spotify User Data:", spotify_user_data)  # Debugging line

        # Extract data
        top_artists = spotify_user_data.get('top_artists', [])
        recently_played = spotify_user_data.get('recently_played', [])
        top_tracks = spotify_user_data.get('top_tracks', [])
        playlists = spotify_user_data.get('playlists', [])
        saved_albums = spotify_user_data.get('saved_albums', [])
        profile = spotify_user_data.get('profile', {})
    except Exception as e:
        spotify_user_data = {
            'error': 'Unable to retrieve data from Spotify',
            'details': str(e)
        }
        print("Error fetching Spotify data:", e)  # Debugging line

        # Set default empty values if an error occurs
        top_artists = []
        recently_played = []
        top_tracks = []
        playlists = []
        saved_albums = []
        profile = {"display_name": "Unknown User", "email": "No email provided"}

    return render(request, 'home_logged_in.html', {
        'spotify_user_data': spotify_user_data,
        'top_artists': top_artists,
        'recently_played': recently_played,
        'top_tracks': top_tracks,
        'playlists': playlists,
        'saved_albums': saved_albums,
        'profile': profile,
    })


@login_required
def profile_view(request):
    if not request.user.is_authenticated or 'spotify_token' not in request.session:
        return redirect('spotify_login')

    access_token = request.session.get('spotify_token')
    if not access_token:
        return redirect('spotify_login')

    try:
        spotify_user_data = get_spotify_data(request)
        print("Spotify User Data:", spotify_user_data)  # Debugging line

        # Extract profile
        profile = spotify_user_data.get('profile', {})
    except Exception as e:
        spotify_user_data = {
            'error': 'Unable to retrieve data from Spotify',
            'details': str(e)
        }
        print("Error:", e)  # Debugging line

        profile = {"display_name": "Unknown User", "email": "No email provided"}

    return render(request, 'profile.html', {
        'profile': profile,  # Directly pass the profile dictionary
        'playlists': spotify_user_data.get('playlists', []),
    })




# View for logged out users
def home_logged_out(request):
    return render(request, 'home_logged_out.html')

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('home_logged_in')  # URL name for the logged-in view
    else:
        return redirect('home_logged_out')  # URL name for the logged-out view

def contact(request):
    return render(request, 'contact.html')

def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect('home_redirect')  # Redirect to home page after logout