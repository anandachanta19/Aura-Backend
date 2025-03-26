from .spotify_auth import refresh_token_if_expired
from ..models import SpotifyToken

def get_spotify_token_by_session(session_key):
    """Retrieve the Spotify token associated with a session key."""
    try:
        token = SpotifyToken.objects.get(session_key=session_key)
        return refresh_token_if_expired(token)
    except SpotifyToken.DoesNotExist:
        print(f"Session key {session_key} not found in database.")
        return None

