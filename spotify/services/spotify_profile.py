from spotipy import Spotify
from .spotify_auth import refresh_token_if_expired
from ..models import SpotifyToken

def get_user_profile(token: SpotifyToken):
    # Fetch the user's Spotify profile information.
    access_token = refresh_token_if_expired(token).access_token
    sp = Spotify(auth=access_token)
    user_profile = sp.current_user()

    return {
        "display_name": user_profile.get("display_name"),
        "email": user_profile.get("email"),
        "followers": user_profile.get("followers", {}).get("total", 0),
        "profile_picture": user_profile.get("images", [{}])[0].get("url"),
    }

def get_user_top_artists(token: SpotifyToken, limit=5):
    # Fetch the user's top artists.
    access_token = refresh_token_if_expired(token).access_token
    sp = Spotify(auth=access_token)
    top_artists_response = sp.current_user_top_artists(limit=limit)

    return [
        artist["name"] for artist in top_artists_response.get("items", [])
    ]

def get_user_playlists(token: SpotifyToken, limit=5):
    # Fetch the user's playlists.
    access_token = refresh_token_if_expired(token)
    sp = Spotify(auth=access_token)
    playlists_response = sp.current_user_playlists(limit=limit)

    return [
        playlist["name"] for playlist in playlists_response.get("items", [])
    ]
