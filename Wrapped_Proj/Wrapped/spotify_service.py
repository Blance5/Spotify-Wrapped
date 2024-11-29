import requests

def refresh_access_token(refresh_token, client_id, client_secret):
    """
    Refresh the Spotify access token using the refresh token.
    """
    url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Error refreshing token: {response.json()}")
        return None

def fetch_spotify_endpoint(url, access_token):
    """
    Fetch data from a Spotify API endpoint.
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching data from {url}: {response.json()}")
        return None
    return response.json()


def get_spotify_data(request, term):
    access_token = request.session.get('spotify_token')
    if not access_token:
        print("Access token is missing or invalid.")
        return {"error": "Access token missing or invalid"}

    headers = {"Authorization": f"Bearer {access_token}"}
    data = {}

    # Fetch Spotify user profile
    try:
        profile_response = requests.get(
            "https://api.spotify.com/v1/me",
            headers=headers
        )
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        # Extract profile details
        data["profile"] = {
            "display_name": profile_data.get("display_name", "Unknown User"),
            "email": profile_data.get("email", "No email provided")
        }
    except Exception as e:
        print("Error fetching profile data:", str(e))
        data["profile"] = {"display_name": "Unknown User", "email": "No email provided"}

    # Fetch top tracks
    try:
        top_tracks_response = requests.get(
            "https://api.spotify.com/v1/me/top/tracks",
            headers=headers,
            params={"limit": 8,
                    "time_range": term}
        )
        top_tracks_response.raise_for_status()
        data["top_tracks"] = [
            {"name": track["name"], "artist": track["artists"][0]["name"]}
            for track in top_tracks_response.json().get("items", [])
        ]
    except Exception as e:
        print("Error fetching top tracks:", str(e))
        data["top_tracks"] = []
   

    # Fetch top artists
    try:
        top_artists_response = requests.get(
            "https://api.spotify.com/v1/me/top/artists",
            headers=headers,
            params={"limit": 5,  # Adjust the number of top artists to fetch (e.g., 10)
                    "time_range": term}
        )
        top_artists_response.raise_for_status()
        data["top_artists"] = [
            {"name": artist["name"], "image_url": artist["images"][0]["url"]}
            for artist in top_artists_response.json().get("items", [])
        ]
    except Exception as e:
        print("Error fetching top artists:", str(e))
        data["top_artists"] = []

        # Fetch playlists
    try:
        playlists_response = requests.get(
            "https://api.spotify.com/v1/me/playlists",
            headers=headers,
            params={"time_range": term} 
        )
        playlists_response.raise_for_status()
        playlists_data = playlists_response.json()

        # Filter out None items
        playlists_items = [playlist for playlist in playlists_data.get("items", []) if playlist is not None]

        # Fetch track count for each playlist and store the name with track count
        playlists_with_track_count = []
        for playlist in playlists_items:
            track_count = playlist.get("tracks", {}).get("total", 0)
            playlists_with_track_count.append({
                "name": playlist.get("name", "Unknown"),
                "track_count": track_count
            })

        # Sort playlists by track count in descending order
        playlists_with_track_count.sort(key=lambda x: x["track_count"], reverse=True)
        playlists_with_track_count = playlists_with_track_count[:5]  # Top 5 playlists

        # Return the sorted playlists
        data["playlists"] = playlists_with_track_count
    except Exception as e:
        print("Error fetching playlists:", str(e))
        data["playlists"] = []


    return data



