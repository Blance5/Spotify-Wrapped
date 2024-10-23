from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Wrapped.views import home_redirect, CustomLogoutView, profile_view

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('', home_redirect, name='home'),  # Home page view
    path('accounts/', include('allauth.urls')),  # Include allauth URLs for authentication
    path('accounts/logout/', CustomLogoutView.as_view(), name='account_logout'),  # Custom logout view
    path('profile/', profile_view, name='profile'),  # New profile URL

    # Include the Wrapped app URLs (this is important)
    path('', include('Wrapped.urls')),  # Include all app-level URLs from Wrapped
]

# Optionally include debug toolbar routes during development
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# Serve static files during development
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
