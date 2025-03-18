import secrets
import spotipy
from django.contrib.auth.models import User
from spotipy.oauth2 import SpotifyOAuth
from django.core.exceptions import PermissionDenied
from ..models import SpotifyToken
from django.utils.timezone import now, timedelta
from ..credentials import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
from spotipy.cache_handler import CacheHandler

class DjangoSessionCacheHandler(CacheHandler):
    def __init__(self, request):
        self.session = request.session

    def get_cached_token(self):
        return self.session.get('spotify_token')

    def save_token_to_cache(self, token_info):
        self.session['spotify_token'] = token_info
        self.session.save()


class SpotifySessionHandler:
    def __init__(self, request):
        self.request = request
        self.session_key = request.session.session_key or request.session.create()
        self.state = self._get_or_generate_state()
        self.auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-email user-read-private user-read-playback-state user-modify-playback-state user-read-currently-playing streaming app-remote-control playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-follow-modify user-follow-read user-library-modify user-library-read user-read-playback-position user-top-read user-read-recently-played ugc-image-upload",
            state=self.state,
            cache_handler=DjangoSessionCacheHandler(self.request),
        )

    def _get_or_generate_state(self):
        """Retrieve existing state or generate a new one."""
        if 'spotify_auth_state' not in self.request.session:
            state = secrets.token_urlsafe(16)
            self.request.session['spotify_auth_state'] = state
            self.request.session.save()
        else:
            state = self.request.session['spotify_auth_state']
        return state

    def get_auth_url(self):
        """Generate authorization URL."""
        return self.auth_manager.get_authorize_url()

    def handle_callback(self):
        """Handle OAuth callback and validate state."""
        # Validate state parameter for CSRF protection
        returned_state = self.request.GET.get('state')
        stored_state = self.request.session.pop('spotify_auth_state', None)

        if not returned_state or returned_state != stored_state:
            raise PermissionDenied("CSRF check failed: State mismatch")

        # Exchange code for token
        if 'code' in self.request.GET:
            token_info = self.auth_manager.get_access_token(self.request.GET['code'])

            # Fetch the Spotify user id
            sp = spotipy.Spotify(auth_manager=self.auth_manager)
            spotify_user = sp.current_user()
            spotify_user_id = spotify_user.get('id')

            # Get or Create User
            user, created = User.objects.get_or_create(username=spotify_user_id)

            # Save token to database, associated with the user
            SpotifyToken.objects.update_or_create(
                user=user,
                defaults={
                    'session_key': self.session_key,
                    'access_token': token_info['access_token'],
                    'refresh_token': token_info['refresh_token'],
                    'expires_at': now() + timedelta(seconds=token_info['expires_in']),
                    'token_type': token_info['token_type']
                }
            )
            return True

        raise PermissionDenied("Spotify auth failed")
