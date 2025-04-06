from .spotify_auth import refresh_token_if_expired
from ..models import SpotifyToken, ActiveSession
from spotipy.oauth2 import SpotifyOAuth
from spotify.models import SpotifyToken
import os
from django.utils import timezone

def get_spotify_token_by_session(session_key):
    """Get Spotify token for a session key if the session is active."""
    # First check if session is active
    active_session = ActiveSession.objects.filter(
        session_key=session_key,
        is_active=True
    ).first()
    
    if not active_session:
        return None

    return SpotifyToken.objects.filter(session_key=session_key).first()

def refresh_spotify_token(token: SpotifyToken) -> SpotifyToken:
    """
    Refresh the Spotify access token using the refresh token.
    """
    try:
        sp_oauth = SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        )
        token_info = sp_oauth.refresh_access_token(token.refresh_token)

        # Update the token in the database
        token.access_token = token_info["access_token"]
        token.expires_at = timezone.now() + timezone.timedelta(seconds=token_info["expires_in"])
        token.save()

        return token
    except Exception as e:
        print(f"Error refreshing Spotify token: {e}")
        raise

