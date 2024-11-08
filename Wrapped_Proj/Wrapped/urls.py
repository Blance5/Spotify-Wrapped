from django.urls import path, include  # include is needed for 'allauth.urls'
from django.conf import settings  # Import settings to check DEBUG mode
from . import views
from .views import profile_view, logout_view  # Import custom views

urlpatterns = [
    
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
    path('home_logged_in/', views.home_logged_in, name='home_logged_in'),  # Logged-in view
    path('home_logged_out/', views.home_logged_out, name='home_logged_out'),  # Logged-out view
    #path('accounts/', include('allauth.urls')),  # Include allauth URLs for authentication
    path('logout/', logout_view, name='logout'),  # Custom logout view
    #path('accounts/email/', views.CustomEmailView.as_view(), name='account_email'),  # Custom email view
    path('profile/', profile_view, name='profile'),  # Add the profile URL here
    path('', views.home_redirect, name='home_redirect'),  # Home page view
]

# Optionally include debug toolbar routes during development
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
