# home/views.py
from django.shortcuts import render, get_object_or_404, redirect
from allauth.account.views import EmailView
from allauth.account.views import LogoutView
from django.views.generic import TemplateView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .spotify_service import get_spotify_data, get_spotify_dataShorten
import requests
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.http import JsonResponse
from django.core.mail import send_mail
import urllib.parse
from django.utils import timezone
from decouple import config
from django.contrib.auth import login, get_user_model
from .models import Wrap
from .models import UserWrappedHistory  # Assuming you're saving the timeframes in a model
from Wrapped.models import UserWrappedHistory
from django.contrib import messages
from django.urls import reverse


from django.db.models import Q #delete later?


SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_CLIENT_ID = config('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = config('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8000/spotify/callback/"
SPOTIFY_USER_PROFILE_URL = "https://api.spotify.com/v1/me"
SCOPES = "user-top-read playlist-read-private user-library-read user-read-email user-read-private"


# def home_view(request):
#   return redirect(request, 'home.html')

def spotify_login(request):
    # request.session.flush()
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
    granted_scopes = token_info.get("scope", "")  # Retrieves granted scopes as a string

    if access_token:
        # Store the access token in the session
        request.session['spotify_token'] = access_token
        request.session['is_authenticated'] = True
        User = get_user_model()
        user, created = User.objects.get_or_create(username="spotify_user")
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return redirect('home_logged_in')
    else:
        print("Failed to obtain access token:", token_info)  # Debugging line
    return redirect('home_logged_out')


# View for logged in users
# @login_required  # Ensures only logged in users can access this view
def home_logged_in(request):
    if not request.user.is_authenticated or 'spotify_token' not in request.session:
        return redirect('spotify_login')

    access_token = request.session.get('spotify_token')
    if not access_token:
        return redirect('spotify_login')
    try:
        spotify_user_data = get_spotify_dataShorten(request)
    except Exception as e:
        spotify_user_data = {
            'error': 'Unable to retrieve data from Spotify',
            'details': str(e)
        }
        print("Error:", e)  # Debugging line

    return render(request, 'home_logged_in.html', {
        'spotify_user_data': spotify_user_data,
    })


@login_required
def wrapped_view(request):
    if not request.user.is_authenticated or 'spotify_token' not in request.session:
        return redirect('spotify_login')

    access_token = request.session.get('spotify_token')
    if not access_token:
        return redirect('spotify_login')
    try:
        term = request.GET.get('term', 'long_term')  # Default to 'long_term'
        spotify_user_data = get_spotify_data(request, term)
    except Exception as e:
        spotify_user_data = {
            'error': 'Unable to retrieve data from Spotify',
            'details': str(e)
        }
        print("Error:", e)  # Debugging line

    # Extract data or provide default empty lists

    top_artists = spotify_user_data.get('top_artists', [])
    recently_played = spotify_user_data.get('recently_played', [])
    top_tracks = spotify_user_data.get('top_tracks', [])
    playlists = spotify_user_data.get('playlists', [])
    saved_albums = spotify_user_data.get('saved_albums', [])
    top_track_popularity_score = spotify_user_data.get('top_track_popularity_score', 0)
    top_track_popularity_message = spotify_user_data.get('top_track_popularity_message',
                                                         'Popularity score not available')
    top_genres = spotify_user_data.get('top_genres', [])
    profile_data = spotify_user_data["profile"]
    country = profile_data.get("country", "Unknown")
    image_url = profile_data.get("image_url", "/static/default_pfp.png")
    followers = profile_data.get("followers", 0)
    user_id = profile_data.get("id", "Unknown")

    display_name = spotify_user_data["profile"]["display_name"]

    # Save the wrap occurrence to the database
    if spotify_user_data.get('error') is None:
        # If we were able to retrieve data, save the new wrap to the database
        user_wrap = UserWrappedHistory(
            user_id=user_id,
            timeframe=term,  # Use the term that was selected by the user
            generated_on=timezone.now(),  # Store the current timestamp

            creator_name=display_name,
            top_artists=top_artists,
            recently_played=recently_played,
            top_tracks=top_tracks,
            playlists=playlists,
            saved_albums=saved_albums,
            top_track_popularity_score=top_track_popularity_score,
            top_track_popularity_message=top_track_popularity_message,
            top_genres=top_genres,
            country=country,
            image_url=image_url,
            followers=followers
        )
        user_wrap.save()

    return render(request, 'wrapped.html', {
        'spotify_user_data': spotify_user_data,
        'top_artists': top_artists,
        'recently_played': recently_played,
        'top_tracks': top_tracks,
        'playlists': playlists,
        'saved_albums': saved_albums,
        'top_track_popularity_score': top_track_popularity_score,
        'top_track_popularity_message': top_track_popularity_message,
        'top_genres': top_genres,
        'country': country,
        'image_url': image_url,
        'followers': followers,
        'user_id': user_id,
        'wrap_id': user_wrap.wrap_id,
    })


# Regenerate Past Wrap
def regenerate_past_wrap(request, wrap_id):
    if not request.user.is_authenticated or 'spotify_token' not in request.session:
        return redirect('spotify_login')

    # Get the user's past wrapped history based on wrap_id (the ID for a specific timeframe)
    wrap = UserWrappedHistory.objects.get(wrap_id=wrap_id)

    access_token = request.session.get('spotify_token')
    if not access_token:
        return redirect('spotify_login')

    try:
        spotify_user_data = get_spotify_dataShorten(request)
    except Exception as e:
        spotify_user_data = {
            'error': 'Unable to retrieve data from Spotify',
            'details': str(e)
        }
        print("Error:", e)  # Debugging line

    # Extract data for rendering
    top_artists = wrap.top_artists
    recently_played = wrap.recently_played
    top_tracks = wrap.top_tracks
    playlists = wrap.playlists
    saved_albums = wrap.saved_albums
    top_track_popularity_score = wrap.top_track_popularity_score
    top_track_popularity_message = wrap.top_track_popularity_message
    display_name = wrap.display_name

    top_genres = wrap.top_genres
    country = wrap.country
    image_url = wrap.image_url
    followers = wrap.followers
    user_id = wrap.user_id

    return render(request, 'wrapped.html', {
        'spotify_user_data': spotify_user_data,
        'top_artists': top_artists,
        'recently_played': recently_played,
        'top_tracks': top_tracks,
        'playlists': playlists,
        'saved_albums': saved_albums,
        'top_track_popularity_score': top_track_popularity_score,
        'top_track_popularity_message': top_track_popularity_message,
        'top_genres': top_genres,
        'country': country,
        'image_url': image_url,
        'followers': followers,
        'user_id': user_id,
        'username': display_name,
        'wrap_id': wrap_id,
    })

def others_wrapped(request, wrap_id):
    spotify_user_data = None
    if request.user.is_authenticated and 'spotify_token' in request.session:
        access_token = request.session.get('spotify_token')
        if not access_token:
            return redirect('spotify_login')

        # Regenerate wrapped data based on the saved timeframe
        try:
            spotify_user_data = get_spotify_dataShorten(request)
        except Exception as e:
            spotify_user_data = {
                'error': 'Unable to retrieve data from Spotify',
                'details': str(e)
            }
            print("Error:", e)  # Debugging line

    # Get the user's past wrapped history based on wrap_id (the ID for a specific timeframe)
    wrap = UserWrappedHistory.objects.get(wrap_id=wrap_id)
    # Extract data for rendering
    top_artists = wrap.top_artists
    recently_played = wrap.recently_played
    top_tracks = wrap.top_tracks
    playlists = wrap.playlists
    saved_albums = wrap.saved_albums
    top_track_popularity_score = wrap.top_track_popularity_score
    top_track_popularity_message = wrap.top_track_popularity_message
    display_name = wrap.creator_name

    top_track_popularity_message = top_track_popularity_message.replace('Your', f"{display_name}'s")
    top_track_popularity_message = top_track_popularity_message.replace('You', 'They')
    top_track_popularity_message = top_track_popularity_message.replace('You\'re ', 'They\'re')
    top_track_popularity_message = top_track_popularity_message.replace('you\'re ', 'they\'re')

    top_genres = wrap.top_genres
    country = wrap.country
    image_url = wrap.image_url
    followers = wrap.followers
    user_id = wrap.user_id

    return render(request, 'others_wrapped.html', {
        'spotify_user_data': spotify_user_data,
        'top_artists': top_artists,
        'recently_played': recently_played,
        'top_tracks': top_tracks,
        'playlists': playlists,
        'saved_albums': saved_albums,
        'top_track_popularity_score': top_track_popularity_score,
        'top_track_popularity_message': top_track_popularity_message,
        'top_genres': top_genres,
        'country': country,
        'image_url': image_url,
        'followers': followers,
        'user_id': user_id,
        'username': display_name,
        'wrap_id': wrap_id,
    })


@login_required
def profile_view(request):
    # Check if the user is authenticated with Spotify
    if not request.user.is_authenticated or 'spotify_token' not in request.session:
        return redirect('spotify_login')

    access_token = request.session.get('spotify_token')
    if not access_token:
        return redirect('spotify_login')

    try:
        # Retrieve Spotify user data
        spotify_user_data = get_spotify_dataShorten(request)
        
        # Extract profile data
        profile_data = spotify_user_data.get("profile", {})
        spotify_user_id = profile_data.get("id", "Unknown")

        # Fetch past wraps, ensuring they match the current Spotify user ID
        past_wraps = UserWrappedHistory.objects.filter(user_id=spotify_user_id).order_by('-generated_on')[:12]

    except Exception as e:
        # Comprehensive error handling
        print(f"Error retrieving Spotify data: {e}")
        messages.error(request, 'Unable to retrieve Spotify data. Please try again later.')
        spotify_user_data = {
            'error': 'Unable to retrieve data from Spotify',
            'details': str(e)
        }
        past_wraps = []


    # Logging for debugging (remove in production)
    print(f"Spotify User ID: {spotify_user_id}")
    print(f"Past Wraps Count: {len(past_wraps)}")

    return render(request, 'profile.html', {
        'spotify_user_data': spotify_user_data,
        'past_wraps': past_wraps,
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
    success_message = None  # To hold success message
    error_message = None  # To hold error message

    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()

        # Validate form data
        if not name or not email or not message:
            error_message = 'All fields are required.'
        else:
            try:
                # Process the message (e.g., send an email)
                recipient_email = getattr(settings, 'EMAIL_HOST_USER', 'wrappeddevs@gmail.com')  # Fallback email
                send_mail(
                    subject=f"Contact Form Submission from {name}",
                    message="from:  " + email + " Message: " + message,
                    from_email=email,
                    recipient_list=[recipient_email],
                    fail_silently=False,
                )
                success_message = 'Thank you for contacting us! We will get back to you soon.'
            except Exception as e:
                print(f"Error sending email: {e}")
                error_message = 'An error occurred while sending your message. Please try again later.'

    # Render the contact page with success or error messages
    return render(request, 'contact.html', {
        'success_message': success_message,
        'error_message': error_message,
    })


def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect('home_redirect')  # Redirect to home page after logout


def delete_wrap(request, wrap_id):
    if request.method == "POST":
        # Find and delete the wrap by wrap_id
        wrap = get_object_or_404(UserWrappedHistory, wrap_id=wrap_id)
        wrap.delete()

    # Redirect back to the profile page
    return redirect('profile')

def make_public(request, wrap_id):
    if request.method == "POST":
        # Find and toggle the wrap by wrap_id
        wrap = get_object_or_404(UserWrappedHistory, wrap_id=wrap_id)
        wrap.public = not wrap.public
        wrap.save()

    # Redirect back to the profile page
    return redirect('profile')

def rename_wrap(request, wrap_id):
    if request.method == "POST":
        new_name = request.POST.get("new_name")
        wrap = get_object_or_404(UserWrappedHistory, wrap_id=wrap_id)
        wrap.name = new_name  # Update the name
        wrap.display_name = new_name  # Update the display name
        wrap.save()
    return redirect('profile')

@login_required
def delete_account(request):
    if request.method == "POST":
        # Get the Spotify User ID from the session or user profile
        try:
            # Attempt to get Spotify user data
            spotify_user_data = get_spotify_data(request, "long_term")
            spotify_user_id = spotify_user_data["profile"].get("id", "Unknown")
            
            # Print out for debugging
            print(f"Deleting wraps for Spotify User ID: {spotify_user_id}")
            
            # Find and delete the wraps
            wraps_to_delete = UserWrappedHistory.objects.filter(user_id=spotify_user_id)
            
            # Print out debug information
            print(f"Number of wraps to delete: {wraps_to_delete.count()}")
            
            # Delete the wraps
            wraps_to_delete.delete()
            
            # Verify deletion
            remaining_wraps = UserWrappedHistory.objects.filter(user_id=spotify_user_id)
            print(f"Remaining wraps after deletion: {remaining_wraps.count()}")
            
            # Delete the user account
            request.user.delete()
            
            # Log out the user
            logout(request)
            
            # Add a success message
            messages.success(request, 'Your account and all associated data have been deleted.')
            
            # Redirect to home page
            return redirect('home')
        
        except Exception as e:
            # Log the full error details
            print(f"Error in delete_account: {str(e)}")
            messages.error(request, f'Error deleting account: {str(e)}')
            return redirect('profile')
    
    # If not a POST request, redirect back to profile
    return redirect('profile')

@login_required
def game_view(request, wrap_id):
    # Uncomment if needed
    # if not request.user.is_authenticated:
    #    return redirect('login')  # Redirect to login if not authenticated

    wrap = get_object_or_404(UserWrappedHistory, wrap_id=wrap_id)
    # get five tracks
    valid_tracks = [track for track in wrap.top_tracks if track["preview_url"]][:5]

    # Check if we have enough tracks
    if len(valid_tracks) < 5:
        messages.warning(request, "Not enough tracks with previews to play the game.")
        previous_page = request.META.get('HTTP_REFERER')
        if previous_page:
            return redirect(previous_page)
        else:
            return redirect(reverse('wrapped_detail', kwargs={'wrap_id': wrap_id}))

    return render(request, "game.html", {
        'top_tracks': valid_tracks,
        'wrap_id': wrap_id,
    })

def public_wrap(request):

    public_wraps = UserWrappedHistory.objects.filter(public=True).order_by('-generated_on')

    search_query = request.GET.get('search', '').strip()
    if search_query:
        public_wraps = public_wraps.filter(
            Q(creator_name__icontains=search_query) |
            Q(display_name__icontains=search_query)
        )

    return render(request, 'public_wrap.html', {
        'public_wraps': public_wraps,
    })
