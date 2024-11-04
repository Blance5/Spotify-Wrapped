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

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8000/spotify/callback"
SPOTIFY_USER_PROFILE_URL = "https://api.spotify.com/v1/me"

#def home_view(request):
 #   return redirect(request, 'home.html')

def spotify_login(request):
    if request.user.is_authenticated:
        return redirect('home_logged_in')
    # Redirect to Spotify's OAuth page
    scopes = "user-read-email"
    query_params = urlencode({
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": scopes,
    })
    auth_url = f"{SPOTIFY_AUTH_URL}?{query_params}"
    return redirect(auth_url)


def spotify_callback(request):
    # Handle the redirect back from Spotify with the authorization code
    code = request.GET.get("code")
    if code:
        # Exchange the authorization code for an access token
        token_response = requests.post(SPOTIFY_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        })
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if access_token:
            # Fetch the user's profile from Spotify
            headers = {"Authorization": f"Bearer {access_token}"}
            profile_response = requests.get(SPOTIFY_USER_PROFILE_URL, headers=headers)
            profile_data = profile_response.json()

            # Extract necessary information
            spotify_id = profile_data.get("id")
            email = profile_data.get("email")

            # Get or create a user in your Django app
            user, created = User.objects.get_or_create(username=spotify_id, defaults={"email": email})
            if created:
                user.set_unusable_password()  # Optional: set an unusable password as Spotify manages auth

            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user, backend=user.backend)

            # Store the access token in session or database if needed
            request.session["spotify_access_token"] = access_token

            return redirect("home_logged_in")  # Redirect to the logged-in home view

    return redirect("home_logged_out")  # Redirect if something goes wrong

# View for logged in users
@login_required  # Ensures only logged in users can access this view
def home_logged_in(request):
     # Check if Spotify access token exists in the session
    if "spotify_access_token" not in request.session:
        return redirect('spotify_login')  # Redirect to Spotify login if no access token

    # Optional: Fetch Spotify user data using the access token
    access_token = request.session["spotify_access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(SPOTIFY_USER_PROFILE_URL, headers=headers)
    spotify_user_data = response.json() if response.status_code == 200 else {}

    return render(request, 'home_logged_in.html', {"spotify_user_data": spotify_user_data})

@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})

# View for logged out users
def home_logged_out(request):
    return render(request, 'home_logged_out.html')

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('home_logged_in')  # URL name for the logged-in view
    else:
        return redirect('home_logged_out')  # URL name for the logged-out view




def logout_view(request):
    logout(request)
    return redirect('home_redirect')  # Redirect to home page after logout