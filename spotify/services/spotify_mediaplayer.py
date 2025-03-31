from spotipy import Spotify
from .spotify_auth import refresh_token_if_expired
from ..models import SpotifyToken

def get_track_details(token, track_id):
    sp = Spotify(auth=refresh_token_if_expired(token).access_token)
    track = sp.track(track_id)
    
    return {
        "id": track["id"],
        "title": track["name"],
        "artist": ", ".join(artist["name"] for artist in track["artists"]),
        "album": track["album"]["name"],
        "albumArt": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
        "duration": track["duration_ms"] // 1000,
        "accessToken": token.access_token,  # Include access token
    }

def get_related_tracks(token, track_id):
    sp = Spotify(auth=refresh_token_if_expired(token).access_token)
    track = sp.track(track_id)
    album_id = track["album"]["id"]  # Use the album ID of the track

    related_tracks = []
    try:
        # Fetch tracks from the same album
        album_tracks = sp.album_tracks(album_id)["items"]
        for album_track in album_tracks:
            # Skip the original track
            if album_track["id"] == track_id:
                continue
            related_tracks.append({
                "id": album_track["id"],
                "title": album_track["name"],
                "artist": ", ".join(artist["name"] for artist in album_track["artists"]),
                "album": track["album"]["name"],
                "albumArt": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                "duration": album_track["duration_ms"] // 1000,
            })
    except Exception as e:
        print(f"Error fetching tracks from album ID {album_id}: {e}")

    return related_tracks
