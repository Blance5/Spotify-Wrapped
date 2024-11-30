import requests
from django.templatetags.static import static


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

        print("PRIFLE DATA::", profile_data)

        # Extract profile details
        image_url = ""
        if profile_data.get("images"):
            # If 'images' is not empty, get the URL of the first image
            
            image_url = profile_data["images"][0].get("url", "")

        if not image_url:
            image_url = static('default_pfp.png')  # Use the default profile image

        # Now add the image_url to the profile data
        data["profile"] = {
            "display_name": profile_data.get("display_name", "Unknown User"),
            "email": profile_data.get("email", "No email provided"),
            "followers": profile_data.get("followers", {}).get("total", 0),
            "country": profile_data.get("country", "Unknown"),
            "image_url": image_url,  # Safely assigned image URL
            "id": profile_data.get("id", "Unknown")
        }

    except Exception as e:
        print("\n\n\n\n\n\n\n\nError fetching profile data:", str(e))
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
        print("Top Tracks:", data["top_tracks"])
    except Exception as e:
        print("Error fetching top tracks:", str(e))
        data["top_tracks"] = []
   

    # Fetch top artists
    try:
        top_artists_response = requests.get(
            "https://api.spotify.com/v1/me/top/artists",
            headers=headers,
            params={"limit": 5, "time_range": term}
        )
        top_artists_response.raise_for_status()
        artists = top_artists_response.json().get("items", [])
        print("\n\n\n\n\n\n")
        for artist in artists:
            print("Artist:", artist["name"], "Popularity:", artist["popularity"])
        data["top_artists"] = [
            {"name": artist["name"], "image_url": artist["images"][0]["url"], "popularity": artist["popularity"]}
            for artist in artists
        ]

        
        # Calculate top genres
        genres = []
        for artist in artists:
            genres.extend(artist.get("genres", []))  # Add genres of each artist
        
        # Count the occurrences of each genre
        genre_count = {}
        for genre in genres:
            genre_count[genre] = genre_count.get(genre, 0) + 1
        
        # Sort genres by frequency and get the top 5
        top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:5]
        data["top_genres"] = [genre[0] for genre in top_genres]  # Extract genre names only


        # Calculate average popularity of the top artists
        if data["top_artists"]:
            average_popularity = sum(artist["popularity"] for artist in data["top_artists"]) / len(data["top_artists"])
            data["top_track_popularity_score"] = average_popularity
        
            # Determine the "basicness" of the music taste
            if average_popularity > 70:
                data["top_track_popularity_message"] = "Your music taste is EXTREMELY mainstream! You're a big fan of the hits."
            elif average_popularity > 60:
                data["top_track_popularity_message"] = "Your music taste is pretty mainstream! You enjoy the popular tracks."
            elif average_popularity > 50:
                data["top_track_popularity_message"] = "Your music taste is somewhere in the middle. Not too basic, not too unique."
            elif average_popularity > 40:
                data["top_track_popularity_message"] = "Your music taste is a little on the unique side... You're a bit of a trendsetter."
            else:
                data["top_track_popularity_message"] = "Your music taste is VERY unique... Maybe you're into some really niche stuff?"

        else:
            data["top_track_popularity_score"] = 0
            data["top_track_popularity_message"] = "Could not determine your music taste."
    except Exception as e:
        print("Error fetching top artists:", str(e))
        data["top_artists"] = []
        data["top_track_popularity_score"] = 0
        data["top_track_popularity_message"] = "Could not fetch your top artists."

        # Fetch playlists
    try:
        playlists_response = requests.get(
            "https://api.spotify.com/v1/me/playlists",
            headers=headers,
            params={"time_range": term} 
        )
        playlists_response.raise_for_status()
        playlists_data = playlists_response.json()
        print("Raw Playlists Response:", playlists_data)  # Debug raw response

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
        print("Sorted Playlists:", data["playlists"])
    except Exception as e:
        print("Error fetching playlists:", str(e))
        data["playlists"] = []


    return data



