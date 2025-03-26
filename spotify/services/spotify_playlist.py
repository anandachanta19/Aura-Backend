from spotipy import Spotify
from .spotify_auth import refresh_token_if_expired
from ..models import SpotifyToken

def get_playlist_details(token: SpotifyToken, playlist_id: str):
    # Fetch details of a specific playlist, including its tracks.
    access_token = refresh_token_if_expired(token).access_token
    sp = Spotify(auth=access_token)

    playlist = sp.playlist(playlist_id)

    return {
        "id": playlist["id"],
        "name": playlist["name"],
        "image_url": playlist["images"][0]["url"] if playlist["images"] else None,
        "songs": [
            {
                "id": track["track"]["id"],
                "title": track["track"]["name"],
                "artist": ", ".join(artist["name"] for artist in track["track"]["artists"]),
                "album": track["track"]["album"]["name"],
                "albumArt": track["track"]["album"]["images"][0]["url"] if track["track"]["album"]["images"] else None,
                "duration": track["track"]["duration_ms"] // 1000,
                "dateAdded": track["added_at"]
            }
            for track in playlist["tracks"]["items"] if track["track"]  # Ensure the track is not None
        ]
    }
