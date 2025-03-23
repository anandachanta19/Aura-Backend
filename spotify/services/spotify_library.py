from spotipy import Spotify
from .spotify_auth import refresh_token_if_expired
from ..models import SpotifyToken

def get_recently_played_tracks(token: SpotifyToken, limit=10):
    # Fetch recently played tracks from Spotify API.
    access_token = refresh_token_if_expired(token)
    sp = Spotify(auth=access_token)

    recently_played = sp.current_user_recently_played(limit=limit)

    return [
        {
            "id": track["track"]["id"],
            "name": track["track"]["name"],
            "artist": ", ".join(artist["name"] for artist in track["track"]["artists"]),
            "album_cover": track["track"]["album"]["images"][0]["url"] if track["track"]["album"]["images"] else None
        }
        for track in recently_played.get("items", [])
    ]

def get_user_playlists(token: SpotifyToken, limit=10):
    # Fetch the user's playlists from Spotify API.
    access_token = refresh_token_if_expired(token)
    sp = Spotify(auth=access_token)

    playlists_response = sp.current_user_playlists(limit=limit)

    return [
        {
            "id": playlist["id"],
            "name": playlist["name"],
            "image_url": playlist["images"][0]["url"] if playlist["images"] else None
        }
        for playlist in playlists_response.get("items", [])
    ]
