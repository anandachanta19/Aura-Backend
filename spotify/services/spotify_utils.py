from .spotify_auth import refresh_token_if_expired
from ..models import SpotifyToken, ActiveSession

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

