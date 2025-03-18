from datetime import timedelta
from django.utils.timezone import now
from spotipy.oauth2 import SpotifyOAuth
from ..models import SpotifyToken
from ..credentials import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

def refresh_token_if_expired(token: SpotifyToken):
    """Refresh the Spotify access token if it has expired."""
    if token.expires_at <= now():
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
        )
        new_token = auth_manager.refresh_access_token(token.refresh_token)

        # Update token fields and save to database
        token.access_token = new_token['access_token']
        token.expires_at = now() + timedelta(seconds=new_token['expires_in'])
        token.save()

    return token.access_token
